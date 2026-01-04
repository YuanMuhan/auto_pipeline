import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

from autopipeline.verifier.rules_loader import load_rules_bundle
from autopipeline.verifier.boundary_checker import BoundaryChecker
from autopipeline.verifier.component_catalog_checker import ComponentCatalogChecker
from autopipeline.utils import load_json, save_json, save_yaml, ensure_dir
from autopipeline.bench.aggregate import aggregate_runs


def _find_latest_pass_run(base_dirs):
    candidates = []
    for base in base_dirs:
        base_path = Path(base)
        if not base_path.exists():
            continue
        for eval_path in base_path.rglob("eval.json"):
            try:
                data = load_json(str(eval_path))
            except Exception:
                continue
            if data.get("overall_status") == "PASS":
                mtime = eval_path.stat().st_mtime
                candidates.append((mtime, eval_path.parent))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _run_boundary(ir_path: Path, rules):
    ir_data = yaml.safe_load(ir_path.read_text(encoding="utf-8")) or {}
    checker = BoundaryChecker(
        forbidden_keywords=rules["ir"]["forbidden_keywords"],
        forbidden_regex=rules["ir"].get("forbidden_regex", []),
    )
    return checker.check_ir(ir_data), ir_data


def _run_catalog(ir_path: Path, base_dir: Path):
    ir_data = yaml.safe_load(ir_path.read_text(encoding="utf-8")) or {}
    checker = ComponentCatalogChecker(str(base_dir))
    res = checker.check_ir(ir_data)
    save_yaml(ir_data, ir_path)  # write back normalized types
    return res, ir_data


def _write_report(out_dir: Path, results):
    lines = ["# PR2 Sanity Report", ""]
    for name, status, msg in results:
        lines.append(f"- {name}: {status} ({msg})")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "PR2_SANITY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    with open(out_dir / "pr2_sanity_results.csv", "w", encoding="utf-8") as f:
        f.write("check,status,message\n")
        for name, status, msg in results:
            f.write(f"{name},{status},{msg}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default=None, help="Existing PASS run directory (contains eval.json)")
    parser.add_argument("--out-dir", default="pr2_sanity_out", help="Output directory for reports")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    ensure_dir(str(out_dir))

    base_dirs = ["outputs", "outputs_runs", "outputs_pr2_runs", "outputs_matrix", "outputs_runs_pr1_bench"]
    run_dir = Path(args.run_dir) if args.run_dir else _find_latest_pass_run(base_dirs)
    if not run_dir or not (run_dir / "eval.json").exists():
        raise SystemExit("No PASS run_dir found; please specify --run-dir")

    eval_data = load_json(str(run_dir / "eval.json"))
    results = []

    # C1 rules_source/hash
    rules = load_rules_bundle()
    src = eval_data.get("rules_version", {}).get("rules_source")
    rules_hash = eval_data.get("llm", {}).get("rules_hash") or rules.get("hash")
    if src == "yaml" and rules_hash:
        results.append(("C1_rules_source", "PASS", f"rules_source={src}, hash={rules_hash}"))
    else:
        results.append(("C1_rules_source", "FAIL", f"rules_source={src}, hash={rules_hash}"))
    results.append(("C1_md_hash_warning", "WARN", "未自动验证 md 改动; 依赖 yaml 优先级生效"))

    ts_dir = out_dir / ".tmp_pr2_sanity" / datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copytree(run_dir, ts_dir)
    ir_path = ts_dir / "ir.yaml"

    # C2 description with HTTP MQTT should not fail
    ir_data = yaml.safe_load(ir_path.read_text(encoding="utf-8")) or {}
    if ir_data.get("components"):
        desc = ir_data["components"][0].get("description", "")
        ir_data["components"][0]["description"] = desc + " HTTP MQTT"
        save_yaml(ir_data, ir_path)
    res_boundary, _ = _run_boundary(ir_path, rules)
    if res_boundary["pass"]:
        results.append(("C2_description_ignore", "PASS", "description not blocked"))
    else:
        results.append(("C2_description_ignore", "FAIL", str(res_boundary.get("failures"))))

    # C3 regex hit
    ir_data = yaml.safe_load(ir_path.read_text(encoding="utf-8")) or {}
    if ir_data.get("components"):
        cfg = ir_data["components"][0].get("config", {}) or {}
        cfg["url"] = "https://example.com"
        ir_data["components"][0]["config"] = cfg
        save_yaml(ir_data, ir_path)
    res_boundary_hit, _ = _run_boundary(ir_path, rules)
    def _code(f):
        return f.code if hasattr(f, "code") else f.get("code")
    def _details(f):
        det = f.details if hasattr(f, "details") else f.get("details", {})
        return det
    boundary_fail = any(_code(f) == "E_BOUNDARY" for f in res_boundary_hit.get("failures", []))
    details_ok = any(_details(f).get("path") and _details(f).get("match") for f in res_boundary_hit.get("failures", []))
    if not res_boundary_hit["pass"] and boundary_fail and details_ok:
        results.append(("C3_boundary_regex", "PASS", f"{res_boundary_hit.get('failures')}"))
    else:
        results.append(("C3_boundary_regex", "FAIL", f"{res_boundary_hit.get('failures')}"))

    # C4 alias normalize
    ir_data = yaml.safe_load(ir_path.read_text(encoding="utf-8")) or {}
    if ir_data.get("components"):
        ir_data["components"][0]["type"] = "processor"
        save_yaml(ir_data, ir_path)
    res_catalog, ir_norm = _run_catalog(ir_path, Path("."))
    norm_type = ir_norm.get("components", [{}])[0].get("type")
    alias_warning = any("normalized" in w for w in res_catalog.get("warnings", []))
    if res_catalog["pass"] and norm_type != "processor" and alias_warning:
        results.append(("C4_alias_normalize", "PASS", f"type normalized to {norm_type}"))
    else:
        results.append(("C4_alias_normalize", "FAIL", f"type={norm_type}, warnings={res_catalog.get('warnings')}"))

    # C5 aggregation includes E_BOUNDARY
    # write a temp eval with boundary failures
    fail_conv = []
    for f in res_boundary_hit.get("failures", []):
        if hasattr(f, "to_dict"):
            fail_conv.append(f.to_dict())
        elif isinstance(f, dict):
            fail_conv.append(f)
    eval_tmp = {
        "case_id": eval_data.get("case_id"),
        "overall_status": "FAIL",
        "overall_static_status": "FAIL",
        "overall_runtime_status": "SKIP",
        "failures_flat": fail_conv,
        "pipeline": {"stages": {"ir": {"duration_ms": 0, "attempts": 1}}, "config": {}},
        "llm": {},
        "checks": {"runtime_compose": {"status": "SKIP", "message": "SKIP"}},
    }
    eval_tmp_path = ts_dir / "eval_boundary.json"
    save_json(eval_tmp, eval_tmp_path)
    summary_csv, summary_err = aggregate_runs([eval_tmp_path], ts_dir)
    err_data = []
    if summary_err.exists():
        with open(summary_err, "r", encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    err_data.append((parts[0], parts[1]))
    has_boundary = any(code == "E_BOUNDARY" and int(cnt) > 0 for code, cnt in err_data)
    if has_boundary:
        results.append(("C5_boundary_aggregated", "PASS", str(err_data)))
    else:
        results.append(("C5_boundary_aggregated", "FAIL", str(err_data)))

    _write_report(out_dir, results)
    print("Sanity checks complete. See", out_dir / "PR2_SANITY_REPORT.md")


if __name__ == "__main__":
    main()
