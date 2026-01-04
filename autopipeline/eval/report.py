"""Report generator (clean version) with static/runtime split."""

from pathlib import Path
from typing import Dict, Any

from autopipeline.utils import save_text


def generate_report(eval_data: Dict[str, Any], output_dir: str) -> str:
    """Generate outputs/<case>/report.md and return path."""
    out_dir = Path(output_dir)
    report_path = out_dir / "report.md"

    status = eval_data.get("overall_status", "UNKNOWN")
    status_static = eval_data.get("overall_static_status", status)
    status_runtime = eval_data.get("overall_runtime_status", "SKIP")
    cfg = (eval_data.get("pipeline") or {}).get("config", {}) or {}
    llm = eval_data.get("llm", {}) or {}
    metrics = eval_data.get("metrics", {}) or {}

    lines = []
    lines.append(f"# Evaluation Report - {eval_data.get('case_id')}")
    lines.append(f"- Status: {status}")
    lines.append(f"- Static: {status_static}")
    lines.append(f"- Runtime: {status_runtime}")
    lines.append(f"- Time: {eval_data.get('timestamp')}")
    lines.append(f"- Output dir: {cfg.get('output_dir')}")
    lines.append(f"- Run id: {cfg.get('run_id')}")
    lines.append("")
    lines.append("## Config")
    lines.append(f"- LLM: provider={llm.get('provider')} model={llm.get('model')} temp={llm.get('temperature')}")
    lines.append(f"- prompt_tier: {cfg.get('prompt_tier')}")
    lines.append(f"- cache_enabled: {cfg.get('cache_enabled')}")
    lines.append(f"- enable_repair: {cfg.get('enable_repair')}")
    lines.append("")
    lines.append("## Metrics")
    lines.append(f"- total_duration_ms: {metrics.get('total_duration_ms')}")
    lines.append(f"- total_attempts: {metrics.get('total_attempts')}")
    lines.append(f"- attempts_by_stage: {metrics.get('attempts_by_stage')}")
    lines.append(f"- tokens_total: {llm.get('usage_tokens_total')}")
    lines.append("")
    lines.append("## Checks (status/message)")
    for name, chk in (eval_data.get("checks") or {}).items():
        lines.append(f"- {name}: {chk.get('status')} ({chk.get('message')})")
    lines.append("")
    sem_warnings = (eval_data.get("validators") or {}).get("semantic_proxy", {}).get("warnings", []) or []
    lines.append("## Semantic Warnings (non-blocking)")
    lines.append(f"- warning_count: {len(sem_warnings)}")
    for w in sem_warnings[:5]:
        if isinstance(w, dict):
            lines.append(f"  - {w.get('code')}: {w.get('message')} details={w.get('details')}")
        else:
            lines.append(f"  - {w}")
    lines.append("")
    lines.append("## Files")
    lines.append(f"- eval.json: {out_dir / 'eval.json'}")
    lines.append(f"- run.log: {out_dir / 'run.log'}")

    save_text("\n".join(lines), str(report_path))
    return str(report_path)
