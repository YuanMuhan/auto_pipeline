import argparse
import json
from pathlib import Path
from typing import List, Dict, Any


def _top_error(failures: List[Dict[str, Any]]) -> str:
    if not failures:
        return ""
    return failures[0].get("code") or ""


def _schema_missing_table(failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for f in failures or []:
        if f.get("code") != "E_SCHEMA_BIND":
            continue
        det = f.get("details", {}) or {}
        rows.append({
            "path": det.get("path") or det.get("instance_path") or "",
            "missing": det.get("missing") or det.get("required") or "",
            "message": (f.get("message") or "").split("\n")[0],
        })
    return rows


def make_report(run_dir: Path, out_subdir: str, out_md: Path, out_json: Path = None):
    before_eval = json.loads((run_dir / "eval.json").read_text(encoding="utf-8"))
    after_eval_path = run_dir / out_subdir / "eval_repaired.json"
    after_eval = json.loads(after_eval_path.read_text(encoding="utf-8"))

    before_top = _top_error(before_eval.get("failures_flat") or [])
    after_top = _top_error(after_eval.get("failures_flat") or [])
    before_missing = _schema_missing_table(before_eval.get("failures_flat") or [])[:5]
    after_missing = _schema_missing_table(after_eval.get("failures_flat") or [])[:5]

    trace_path = run_dir / out_subdir / "repair_trace.json"
    trace = []
    if trace_path.exists():
        trace = json.loads(trace_path.read_text(encoding="utf-8"))

    lines = []
    lines.append(f"# Bindings Repair Before/After ({run_dir.name})\n")
    lines.append(f"- run_dir: `{run_dir}`")
    lines.append(f"- replay_dir: `{run_dir / out_subdir}`")
    lines.append(f"- before top_error: {before_top or 'NONE'}")
    lines.append(f"- after top_error: {after_top or 'NONE'}\n")

    lines.append("## Before: schema bind missing fields (Top 5)\n")
    if before_missing:
        lines.append("| path | missing/required | message |")
        lines.append("|---|---|---|")
        for r in before_missing:
            lines.append(f"| {r['path']} | {r['missing']} | {r['message']} |")
    else:
        lines.append("无 E_SCHEMA_BIND 详情\n")

    lines.append("\n## After: schema bind missing fields (Top 5)\n")
    if after_missing:
        lines.append("| path | missing/required | message |")
        lines.append("|---|---|---|")
        for r in after_missing:
            lines.append(f"| {r['path']} | {r['missing']} | {r['message']} |")
    else:
        lines.append("无 E_SCHEMA_BIND 详情\n")

    lines.append("\n## Repair Trace 摘要\n")
    if trace:
        for t in trace:
            lines.append(f"- attempt={t.get('attempt')} strategy={t.get('strategy')} "
                         f"patch_actions={t.get('patch_actions_count')} hints={t.get('used_hints_count')} "
                         f"artifact={t.get('artifact_written')}")
    else:
        lines.append("无 repair_trace\n")

    lines.append("\n## After Error Explanation\n")
    after_failures = after_eval.get("failures_flat") or []
    if after_top:
        top_checker = after_failures[0].get("checker") if after_failures else ""
        msg = (after_failures[0].get("message") or "").split("\n")[0] if after_failures else ""
        lines.append(f"- top_error: {after_top}, checker: {top_checker}, message: {msg}")
        if after_top == "E_UNKNOWN":
            dbg_path = run_dir / out_subdir / "debug_unknown.json"
            if dbg_path.exists():
                dbg = json.loads(dbg_path.read_text(encoding="utf-8"))
                lines.append(f"- E_UNKNOWN 详情: {dbg.get('failures')}")
            lines.append("- 建议：检查回放目录是否缺少生成产物；已在回放中注入 stub manifest/main/compose，若仍 E_UNKNOWN 则需要改进异常归因。")
    else:
        lines.append("- after 已 PASS（无 top_error）")

    lines.append("\n## 生成的文件\n")
    lines.append(f"- {run_dir/out_subdir/'bindings_patched_attempt1.yaml'}")
    lines.append(f"- {run_dir/out_subdir/'bindings_norm.yaml'}")
    lines.append(f"- {run_dir/out_subdir/'eval_repaired.json'}")
    lines.append(f"- {run_dir/out_subdir/'repair_trace.json'}")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")

    if out_json:
        debug = {
            "before_top_error": before_top,
            "after_top_error": after_top,
            "before_missing_fields_topk": before_missing,
            "after_failures_topk": [{"code": f.get("code"), "checker": f.get("checker"), "message": (f.get("message") or '').split('\\n')[0]} for f in after_failures[:5]],
        }
        if after_top == "E_UNKNOWN":
            dbg_path = run_dir / out_subdir / "debug_unknown.json"
            if dbg_path.exists():
                debug["unknown_debug"] = json.loads(dbg_path.read_text(encoding="utf-8"))
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(debug, indent=2, ensure_ascii=False), encoding="utf-8")

    return out_md


def main():
    parser = argparse.ArgumentParser(description="Generate before/after repair report")
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--out_subdir", default="replay_repair")
    parser.add_argument("--out_md", default="reports/repair/bindings_repair_before_after.md")
    parser.add_argument("--out_json", default="reports/repair/bindings_repair_debug.json")
    args = parser.parse_args()

    make_report(Path(args.run_dir), args.out_subdir, Path(args.out_md), Path(args.out_json) if args.out_json else None)
    print(f"Report written to {args.out_md}")


if __name__ == "__main__":
    main()
