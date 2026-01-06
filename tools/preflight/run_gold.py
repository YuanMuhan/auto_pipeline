import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from autopipeline.eval.evaluate_artifacts import evaluate_run_dir
from autopipeline.utils import ensure_dir


def _read_expected(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _extract_error_codes(eval_result: Dict[str, Any]) -> List[str]:
    codes = []
    for failure in eval_result.get("failures_flat", []):
        code = failure.get("code")
        if code:
            codes.append(code)
    return codes


def _evaluate_case(case_dir: Path, base_dir: str, gate_mode: str) -> Dict[str, Any]:
    eval_result = evaluate_run_dir(case_dir, base_dir=base_dir, runtime_check=False,
                                   enable_catalog=True, gate_mode=gate_mode)
    errors = _extract_error_codes(eval_result)
    fail_stage = None
    if eval_result.get("failures_flat"):
        fail_stage = eval_result["failures_flat"][0].get("stage")
    return {
        "eval": eval_result,
        "overall_status": eval_result.get("overall_status"),
        "error_codes": errors,
        "fail_stage": fail_stage,
    }


def _compare(expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, List[str]]:
    mismatches = []
    exp_status = expected.get("expected_status")
    if exp_status and str(exp_status).upper() != str(actual["overall_status"]).upper():
        mismatches.append(f"status expected={exp_status} actual={actual['overall_status']}")

    exp_codes = expected.get("expected_error_codes")
    if exp_codes:
        actual_codes = set(actual["error_codes"])
        missing = [c for c in exp_codes if c not in actual_codes]
        if missing:
            mismatches.append(f"missing expected_error_codes={missing}")

    exp_stage = expected.get("expected_fail_stage")
    if exp_stage and exp_stage != actual.get("fail_stage"):
        mismatches.append(f"fail_stage expected={exp_stage} actual={actual.get('fail_stage')}")
    return (len(mismatches) == 0), mismatches


def run_gold(gold_dir: Path, out_dir: Path, base_dir: str = ".", gate_mode: str = "core") -> Dict[str, Any]:
    ensure_dir(out_dir)
    cases = sorted([p for p in gold_dir.iterdir() if p.is_dir()])
    results = []
    for case_dir in cases:
        expected = _read_expected(case_dir / "expected.json")
        actual = _evaluate_case(case_dir, base_dir=base_dir, gate_mode=gate_mode)
        passed, mismatches = _compare(expected, actual)
        results.append({
            "case": case_dir.name,
            "expected": expected,
            "actual_status": actual["overall_status"],
            "actual_error_codes": actual["error_codes"],
            "actual_fail_stage": actual["fail_stage"],
            "passed": passed,
            "mismatches": mismatches,
        })

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "results": results,
    }
    out_json = out_dir / "gold_results.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Preflight Gold Tests Report",
        "",
        f"Total: {summary['total']}  Passed: {summary['passed']}  Failed: {summary['failed']}",
        "",
        "| case | expected_status | actual_status | expected_codes | actual_codes | result | notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        exp_status = r["expected"].get("expected_status", "")
        exp_codes = r["expected"].get("expected_error_codes", [])
        notes = "; ".join(r["mismatches"]) if r["mismatches"] else ""
        lines.append(
            f"| {r['case']} | {exp_status} | {r['actual_status']} | {exp_codes} | "
            f"{r['actual_error_codes']} | {'PASS' if r['passed'] else 'FAIL'} | {notes} |"
        )
    (out_dir / "gold_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run preflight gold tests without LLM")
    parser.add_argument("--gold_dir", type=str, default="tests/gold", help="Directory containing gold cases")
    parser.add_argument("--out_dir", type=str, default="reports/preflight", help="Output directory for reports")
    parser.add_argument("--gate_mode", type=str, default="core", help="Gate mode: core or full")
    parser.add_argument("--base_dir", type=str, default=".", help="Repository root for case fallbacks")
    args = parser.parse_args()
    gold_dir = Path(args.gold_dir)
    out_dir = Path(args.out_dir)
    summary = run_gold(gold_dir, out_dir, base_dir=args.base_dir, gate_mode=args.gate_mode)
    print(f"[gold] completed: {summary['passed']}/{summary['total']} passed. Report: {out_dir/'gold_report.md'}")


if __name__ == "__main__":
    main()
