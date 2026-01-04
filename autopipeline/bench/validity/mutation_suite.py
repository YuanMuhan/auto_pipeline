"""Mutation suite runner for validators without LLM calls."""

import argparse
import os
import shutil
from pathlib import Path
from datetime import datetime
import csv
from collections import Counter

from autopipeline.eval.evaluate_artifacts import evaluate_run_dir
from autopipeline.bench.validity.mutations import get_mutations
from autopipeline.utils import ensure_dir, load_json, save_json


def _find_seed(base_dirs):
    candidates = []
    for base in base_dirs:
        p = Path(base)
        if not p.exists():
            continue
        for eval_path in p.rglob("eval.json"):
            try:
                data = load_json(eval_path)
            except Exception:
                continue
            if data.get("overall_status") == "PASS":
                candidates.append((eval_path.stat().st_mtime, eval_path.parent))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _error_top(eval_data):
    errs = eval_data.get("failures_flat", []) or []
    counter = Counter([e.get("code", "") for e in errs])
    if not counter:
        return ""
    return counter.most_common(1)[0][0]


def run_suite(seed_dir: Path, out_root: Path, max_mutations: int = None):
    mutations = get_mutations()
    if max_mutations:
        mutations = mutations[:max_mutations]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = out_root / f"run_{ts}"
    ensure_dir(str(out_dir))

    # copy seed
    seed_copy = out_dir / "seed"
    shutil.copytree(seed_dir, seed_copy)
    # ensure user_problem/device_info present in seed_copy/inputs (self-contained)
    case_id = seed_dir.parent.name
    case_dir = Path("cases") / case_id
    inputs_dir = seed_copy / "inputs"
    ensure_dir(inputs_dir)
    seed_input_source = "run_dir/inputs"
    for fname in ["user_problem.json", "device_info.json"]:
        dst = inputs_dir / fname
        if dst.exists():
            continue
        src = seed_dir / "inputs" / fname
        if src.exists():
            shutil.copy(src, dst)
            continue
        legacy = seed_dir / fname
        if legacy.exists():
            shutil.copy(legacy, dst)
            continue
        if case_dir.exists() and (case_dir / fname).exists():
            shutil.copy(case_dir / fname, dst)
            seed_input_source = "fallback:cases"

    rows = []
    error_counter = Counter()
    for mut in mutations:
        mut_dir = out_dir / "mutations" / mut.id
        shutil.copytree(seed_copy, mut_dir)
        mut.apply_fn(mut_dir)
        try:
            eval_dict = evaluate_run_dir(mut_dir)
        except Exception as e:
            eval_dict = {
                "overall_status": "FAIL",
                "overall_static_status": "FAIL",
                "overall_runtime_status": "SKIP",
                "checks": {"runtime_compose": {"status": "SKIP", "message": "SKIP"}},
                "failures_flat": [{"code": "E_UNKNOWN", "stage": "mutator", "checker": mut.id, "message": str(e)}],
            }
        save_json(eval_dict, mut_dir / "mutation_eval.json")

        failed_checks = [k for k, v in (eval_dict.get("checks") or {}).items() if v.get("status") == "FAIL"]
        top_error = _error_top(eval_dict)
        error_counter[top_error] += 1 if top_error else 0

        hit = False
        overshadowed = ""
        if mut.expect_pass:
            hit = eval_dict.get("overall_status") == "PASS"
            if not hit:
                overshadowed = ",".join(failed_checks)
        else:
            if mut.expected_check and mut.expected_check in failed_checks:
                hit = True
            if mut.expected_code and top_error == mut.expected_code:
                hit = True
            if not hit and failed_checks:
                overshadowed = failed_checks[0]

        rows.append({
            "mutation_id": mut.id,
            "description": mut.desc,
            "expected_check": mut.expected_check,
            "expected_code": mut.expected_code,
            "expect_pass": mut.expect_pass,
            "hit": hit,
            "overshadowed_by": overshadowed,
            "overall_status": eval_dict.get("overall_status"),
            "overall_static_status": eval_dict.get("overall_static_status"),
            "failed_checks": ";".join(failed_checks),
            "error_code_top1": top_error,
            "failures_count": len(eval_dict.get("failures_flat", [])),
            "notes": "",
        })

    summary_path = out_dir / "mutation_results.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary_err_path = out_dir / "mutation_summary_by_error.csv"
    with open(summary_err_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["error_code", "count"])
        for code, cnt in error_counter.most_common():
            w.writerow([code, cnt])

    report_lines = ["# Mutation Report", "", f"* seed_dir: {seed_dir}", f"* seed_input_source: {seed_input_source}", ""]
    for r in rows:
        status = "HIT" if r["hit"] else "MISS"
        report_lines.append(f"## {r['mutation_id']} ({status})")
        report_lines.append(f"- desc: {r['description']}")
        report_lines.append(f"- expected: check={r['expected_check']} code={r['expected_code']} expect_pass={r['expect_pass']}")
        report_lines.append(f"- overall: {r['overall_static_status']}")
        report_lines.append(f"- failed_checks: {r['failed_checks']}")
        report_lines.append(f"- error_code_top1: {r['error_code_top1']}")
        if r["overshadowed_by"]:
            report_lines.append(f"- overshadowed_by: {r['overshadowed_by']}")
        report_lines.append("")
    (out_dir / "mutation_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    print("Mutation suite complete. Results in", out_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default=None, help="Seed PASS run dir (contains eval.json)")
    parser.add_argument("--out-dir", default="mutation_out", help="Output root for mutations")
    parser.add_argument("--max-mutations", type=int, default=None)
    args = parser.parse_args()

    seed = Path(args.run_dir) if args.run_dir else _find_seed(["outputs_pr2_runs", "outputs_runs", "outputs", "outputs_matrix"])
    if not seed or not (seed / "eval.json").exists():
        raise SystemExit("No seed run_dir found; please specify --run-dir")
    run_suite(seed, Path(args.out_dir), args.max_mutations)


if __name__ == "__main__":
    main()
