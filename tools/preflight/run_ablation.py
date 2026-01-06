import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Any, List, Tuple

from autopipeline.eval.evaluate_artifacts import evaluate_run_dir
from autopipeline.utils import ensure_dir


def find_run_dirs(base_dir: Path, case_names: List[str]) -> List[Path]:
    plan_files = list(base_dir.rglob("plan.json"))
    run_dirs = []
    for plan in plan_files:
        run_dir = plan.parent
        case_id = run_dir.parent.name
        if case_names and case_id not in case_names:
            continue
        run_dirs.append(run_dir)
    return sorted(run_dirs)


def top_error_codes(eval_result: Dict[str, Any]) -> List[str]:
    codes = []
    for f in eval_result.get("failures_flat", []):
        code = f.get("code")
        if code:
            codes.append(code)
    if not codes:
        return []
    counter = Counter(codes)
    max_count = max(counter.values())
    return [c for c, cnt in counter.items() if cnt == max_count]


def evaluate_mode(mode_name: str, run_dirs: List[Path], enable_catalog: bool, gate_mode: str = "core",
                  catalog_strict: bool = False) -> Dict[str, Any]:
    rows = []
    error_counter = Counter()
    checker_counter = Counter()
    pass_count = 0
    for run_dir in run_dirs:
        res = evaluate_run_dir(run_dir, base_dir=".", runtime_check=False, enable_catalog=enable_catalog,
                               gate_mode=gate_mode, catalog_strict=catalog_strict)
        status = res.get("overall_status", "FAIL")
        if status == "PASS":
            pass_count += 1
        codes = top_error_codes(res)
        for c in codes:
            error_counter[c] += 1
        for f in res.get("failures_flat", []):
            chk = f.get("checker")
            if chk:
                checker_counter[chk] += 1
        rows.append({
            "run_dir": str(run_dir),
            "case_id": run_dir.parent.name,
            "mode": mode_name,
            "status": status,
            "top_error_codes": codes,
        })
    summary = {
        "mode": mode_name,
        "total": len(rows),
        "pass": pass_count,
        "fail": len(rows) - pass_count,
        "top_errors": error_counter.most_common(),
        "top_checkers": checker_counter.most_common(),
        "rows": rows,
    }
    return summary


def run_ablation(run_dirs: List[Path], out_dir: Path, modes: List[str]):
    ensure_dir(out_dir)
    summaries = []
    for mode in modes:
        mode_lower = mode.lower()
        if mode_lower in ("baseline", "catalog_open"):
            summaries.append(evaluate_mode(mode_lower, run_dirs, enable_catalog=True, gate_mode="core",
                                           catalog_strict=False))
        elif mode_lower == "catalog_strict":
            summaries.append(evaluate_mode(mode_lower, run_dirs, enable_catalog=True, gate_mode="core",
                                           catalog_strict=True))
        elif mode_lower == "gate_core":
            summaries.append(evaluate_mode(mode_lower, run_dirs, enable_catalog=True, gate_mode="core",
                                           catalog_strict=False))
        elif mode_lower == "gate_full":
            summaries.append(evaluate_mode(mode_lower, run_dirs, enable_catalog=True, gate_mode="full",
                                           catalog_strict=False))
        else:
            raise ValueError(f"Unknown mode {mode}")

    out_json = out_dir / "ablation.json"
    out_json.write_text(json.dumps({"summaries": summaries}, indent=2), encoding="utf-8")

    lines = [
        "# Preflight Ablation",
        "",
        "| mode | total | pass | fail | top_errors | top_checkers |",
        "|---|---|---|---|---|---|",
    ]
    for s in summaries:
        top_err = s["top_errors"][:3]
        top_chk = s.get("top_checkers", [])[:3]
        lines.append(f"| {s['mode']} | {s['total']} | {s['pass']} | {s['fail']} | {top_err} | {top_chk} |")
    lines.append("")
    lines.append("## Details")
    lines.append("| case | mode | status | top_error_codes | run_dir |")
    lines.append("|---|---|---|---|---|")
    for s in summaries:
        for row in s["rows"]:
            lines.append(
                f"| {row['case_id']} | {row['mode']} | {row['status']} | {row['top_error_codes']} | {row['run_dir']} |"
            )
    (out_dir / "ablation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run minimal ablation (catalog on/off)")
    parser.add_argument("--base_dir", type=str, default="outputs_preflight", help="Root containing run dirs")
    parser.add_argument("--case_names", type=str, default="", help="Comma separated case ids to include")
    parser.add_argument("--modes", type=str, default="baseline,current", help="Comma separated modes")
    parser.add_argument("--out_dir", type=str, default="reports/preflight", help="Output directory for reports")
    args = parser.parse_args()
    case_names = [c for c in args.case_names.split(",") if c] if args.case_names else []
    base_dir = Path(args.base_dir)
    run_dirs = find_run_dirs(base_dir, case_names)
    if not run_dirs:
        print(f"No run dirs found under {base_dir}")
        return
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    run_ablation(run_dirs, Path(args.out_dir), modes)
    print(f"[ablation] completed. Outputs in {args.out_dir}")


if __name__ == "__main__":
    main()
