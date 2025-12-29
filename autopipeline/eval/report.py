"""Human-readable report generator for pipeline runs."""

from collections import Counter
from pathlib import Path
from typing import Dict, Any, List

from autopipeline.utils import save_text


def _artifact_presence(output_dir: Path) -> List[str]:
    expected = [
        "plan.json",
        "ir.yaml",
        "bindings.yaml",
        "generated_code/manifest.json",
        "docker-compose.yml",
    ]
    lines = []
    for rel in expected:
        path = output_dir / rel
        status = "OK" if path.exists() else "MISSING"
        lines.append(f"- [{status}] {rel}")
    return lines


def _summarize_failures(eval_data: Dict[str, Any], top_n: int = 5) -> List[str]:
    failures = eval_data.get("failures_flat", []) or []
    if not failures:
        return ["- 无失败（全部通过）"]
    counter = Counter([f.get("code", "E_UNKNOWN") for f in failures])
    lines = []
    for code, count in counter.most_common(top_n):
        lines.append(f"- {code}: {count} 次")
    return lines


def generate_report(eval_data: Dict[str, Any], output_dir: str) -> str:
    """Generate outputs/<case>/report.md and return path."""
    out_dir = Path(output_dir)
    report_path = out_dir / "report.md"

    case_id = eval_data.get("case_id")
    llm = eval_data.get("llm", {})
    status = eval_data.get("overall_status", "UNKNOWN")
    failures_lines = _summarize_failures(eval_data)
    artifacts = _artifact_presence(out_dir)
    llm_calls = llm.get("calls_total", 0)
    cache_hits = llm.get("cache_hits", 0)
    cache_misses = llm.get("cache_misses", 0)
    usage_tokens = llm.get("usage_tokens_total")

    content = []
    content.append(f"# Evaluation Report - {case_id}")
    content.append(f"- 状态: **{status}**")
    content.append(f"- 时间: {eval_data.get('timestamp')}")
    content.append(f"- ESR: {'1' if status == 'PASS' else '0'}")
    content.append("")
    content.append("## Case 信息")
    content.append(f"- LLM: provider={llm.get('provider')} model={llm.get('model')} temperature={llm.get('temperature')}")
    content.append(f"- rules_hash: {llm.get('rules_hash')}")
    content.append(f"- catalog_hashes: {eval_data.get('catalog_hashes')}")
    content.append("")
    content.append("## 失败 Top-N（按 error_code）")
    content.extend(failures_lines)
    content.append("")
    content.append("## LLM 统计")
    content.append(f"- calls_total: {llm_calls}, cache_hits: {cache_hits}, cache_misses: {cache_misses}")
    if usage_tokens is not None:
        content.append(f"- usage_tokens_total: {usage_tokens}")
    content.append("")
    content.append("## 产物存在性")
    content.extend(artifacts)
    content.append("")
    content.append("## 日志与文件")
    content.append(f"- eval.json: {out_dir / 'eval.json'}")
    content.append(f"- run.log: {out_dir / 'run.log'}")

    save_text("\n".join(content), str(report_path))
    return str(report_path)
