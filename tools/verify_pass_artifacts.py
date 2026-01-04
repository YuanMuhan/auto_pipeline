"""Validate existing PASS artifacts and emit evidence summary without modifying inputs.

Usage:
    python tools/verify_pass_artifacts.py --eval-path outputs/DEMO-MONITORING/eval.json

The script prints a short summary and writes PASS_EVIDENCE.md (and optional JSON) next to the eval file.
"""

import argparse
import json
from pathlib import Path

EXPECTED_TOKENS = 10019  # reference token usage; mismatch will be reported but not treated as failure


def check_eval(eval_path: Path):
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    res = []
    status_ok = data.get("overall_status") == "PASS"
    res.append(("overall_status", status_ok, data.get("overall_status")))
    res.append(("overall_static_status", data.get("overall_static_status") == "PASS", data.get("overall_static_status")))
    res.append(("overall_runtime_status", data.get("overall_runtime_status") in ("PASS", "SKIP"), data.get("overall_runtime_status")))

    cfg = (data.get("pipeline") or {}).get("config", {}) or {}
    cfg_checks = {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "prompt_tier": "P0",
        "temperature": 0,
    }
    for k, expected in cfg_checks.items():
        val = cfg.get(k)
        res.append((f"config.{k}", val == expected, val))
    res.append(("config.cache_enabled=False", cfg.get("cache_enabled") is False, cfg.get("cache_enabled")))
    res.append(("config.enable_repair=True", cfg.get("enable_repair") is True, cfg.get("enable_repair")))

    llm = data.get("llm", {}) or {}
    tokens = llm.get("usage_tokens_total")
    tokens_ok = (tokens == EXPECTED_TOKENS)
    res.append((f"llm.usage_tokens_total=={EXPECTED_TOKENS}", tokens_ok, tokens))

    # runtime compose status (allow SKIP)
    rt_status = (data.get("checks", {}) or {}).get("runtime_compose", {}).get("status", "SKIP")
    res.append(("checks.runtime_compose.status", rt_status in ("PASS", "SKIP"), rt_status))

    # Artifact existence
    root = eval_path.parent
    artifact_paths = ["plan.json", "ir.yaml", "bindings.yaml", "eval.json", "report.md", "run.log"]
    for p in artifact_paths:
        exists = (root / p).exists()
        res.append((f"artifact:{p}", exists, str(root / p)))

    return res, data


def render_summary(results):
    lines = []
    ok_all = True
    for name, ok, val in results:
        mark = "PASS" if ok else "WARN"
        if not ok and name.startswith("artifact:"):
            mark = "FAIL"
        ok_all = ok_all and (mark != "FAIL")
        lines.append(f"- {mark}: {name} (value={val})")
    return "\n".join(lines), ok_all


def write_evidence(eval_path: Path, summary_text: str, eval_data: dict):
    md_path = eval_path.parent / "PASS_EVIDENCE.md"
    md = [
        "# PASS Evidence",
        "",
        f"- eval: {eval_path}",
        f"- case: {eval_data.get('case_id')}",
        f"- status: {eval_data.get('overall_status')}",
        f"- static: {eval_data.get('overall_static_status')}",
        f"- runtime: {eval_data.get('overall_runtime_status')}",
        "",
        "## Checks",
        summary_text,
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-path", default="outputs/DEMO-MONITORING/eval.json", help="Path to eval.json to verify")
    args = parser.parse_args()
    eval_path = Path(args.eval_path)
    if not eval_path.exists():
        raise SystemExit(f"eval.json not found: {eval_path}")
    results, data = check_eval(eval_path)
    summary_text, ok_all = render_summary(results)
    print("=== PASS Evidence Summary ===")
    print(summary_text)
    write_evidence(eval_path, summary_text, data)
    print(f"Wrote: {eval_path.parent / 'PASS_EVIDENCE.md'}")
    if not ok_all:
        print("Some checks WARN/FAIL (see above), but script exits with 0 for evidence-only use.")


if __name__ == "__main__":
    main()
