"""Aggregate multiple eval.json files into CSV summaries."""

import csv
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any

from autopipeline.utils import load_json, ensure_dir


def _summarize_eval(eval_data: Dict[str, Any], eval_path: Path) -> Dict[str, Any]:
    failures = eval_data.get("failures_flat", []) or []
    fail_codes = Counter([f.get("code", "E_UNKNOWN") for f in failures])
    pipeline = eval_data.get("pipeline", {}).get("stages", {})
    duration_total = sum(stage.get("duration_ms", 0) for stage in pipeline.values())
    attempts = [stage.get("attempts", 0) for stage in pipeline.values() if stage.get("attempts") is not None]
    avg_attempts = sum(attempts) / len(attempts) if attempts else 0
    row = {
        "eval_path": str(eval_path),
        "case_id": eval_data.get("case_id"),
        "status": eval_data.get("overall_status"),
        "pass": 1 if eval_data.get("overall_status") == "PASS" else 0,
        "fail_codes": ";".join([code for code, _ in fail_codes.most_common(3)]),
        "duration_ms_total": duration_total,
        "attempts_avg": avg_attempts,
        "llm_calls": eval_data.get("llm", {}).get("calls_total"),
        "cache_hits": eval_data.get("llm", {}).get("cache_hits"),
        "cache_misses": eval_data.get("llm", {}).get("cache_misses"),
        "provider": eval_data.get("llm", {}).get("provider"),
        "model": eval_data.get("llm", {}).get("model"),
        "ir_attempts": pipeline.get("ir", {}).get("attempts"),
        "bindings_attempts": pipeline.get("bindings", {}).get("attempts"),
        "rules_hash": eval_data.get("llm", {}).get("rules_hash"),
        "catalog_hashes": eval_data.get("catalog_hashes"),
    }
    return row


def aggregate_runs(eval_paths: List[Path], out_root: Path):
    """Aggregate eval.json files into summary CSVs. Returns tuple of csv paths."""
    ensure_dir(str(out_root))
    summary_rows = []
    error_counter = Counter()
    for path in eval_paths:
        data = load_json(str(path))
        summary_rows.append(_summarize_eval(data, path))
        for f in data.get("failures_flat", []) or []:
            error_counter[f.get("code", "E_UNKNOWN")] += 1

    summary_path = out_root / "summary.csv"
    if summary_rows:
        fieldnames = list(summary_rows[0].keys())
        with open(summary_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)
    else:
        summary_path.touch()

    summary_error_path = out_root / "summary_by_error.csv"
    with open(summary_error_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["error_code", "count"])
        for code, cnt in error_counter.most_common():
            writer.writerow([code, cnt])

    return summary_path, summary_error_path
