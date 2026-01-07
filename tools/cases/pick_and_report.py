import argparse
import json
import glob
import shutil
from pathlib import Path
from collections import Counter
from typing import Any, Dict, List, Optional

from autopipeline.utils import ensure_dir, load_json
import yaml


def _load_eval(run_dir: Path) -> Optional[Dict[str, Any]]:
    eval_path = run_dir / "eval.json"
    if not eval_path.exists():
        return None
    try:
        return load_json(eval_path)
    except Exception:
        return None


def _top_errors(eval_result: Dict[str, Any], top_n: int = 3) -> List[str]:
    codes = []
    for f in eval_result.get("failures_flat", []):
        code = f.get("code")
        if code:
            codes.append(code)
    if not codes:
        return []
    counter = Counter(codes)
    return [c for c, _ in counter.most_common(top_n)]


def _warnings_count(eval_result: Dict[str, Any]) -> int:
    total = 0
    for res in eval_result.get("validators", {}).values():
        total += len(res.get("warnings", []) or [])
    total += len(eval_result.get("input_validation", []) or [])
    return total


def _tokens(eval_result: Dict[str, Any]) -> Optional[float]:
    llm = eval_result.get("llm", {}) or {}
    if "usage_tokens_total" in llm:
        return llm.get("usage_tokens_total")
    metrics = eval_result.get("metrics", {}) or {}
    if "tokens_total" in metrics:
        return metrics.get("tokens_total")
    return None


def _calls(eval_result: Dict[str, Any]) -> Optional[int]:
    llm = eval_result.get("llm", {}) or {}
    if "calls_total" in llm:
        return llm.get("calls_total")
    return None


def _duration_ms(eval_result: Dict[str, Any]) -> Optional[float]:
    metrics = eval_result.get("metrics", {}) or {}
    if "total_duration_ms" in metrics:
        return metrics.get("total_duration_ms")
    if "total_time_s" in metrics:
        return metrics.get("total_time_s") * 1000
    return None


def _attempts(eval_result: Dict[str, Any]) -> Optional[int]:
    metrics = eval_result.get("metrics", {}) or {}
    if "total_attempts" in metrics:
        return metrics.get("total_attempts")
    return None


def _artifacts(run_dir: Path) -> Dict[str, bool]:
    bindings_present = False
    for name in ["bindings.yaml", "bindings_raw.yaml", "bindings_raw.txt"]:
        if (run_dir / name).exists():
            bindings_present = True
            break
    return {
        "plan": (run_dir / "plan.json").exists(),
        "ir": (run_dir / "ir.yaml").exists(),
        "bindings": bindings_present,
        "eval": (run_dir / "eval.json").exists(),
    }


def _core_status(eval_result: Dict[str, Any]) -> str:
    return eval_result.get("overall_core_status") or eval_result.get("overall_static_status") or eval_result.get("overall_status", "FAIL")


def _exec_status(eval_result: Dict[str, Any]) -> str:
    return eval_result.get("overall_exec_status") or eval_result.get("overall_runtime_status") or "SKIP"


def _app_name(run_dir: Path, eval_result: Dict[str, Any]) -> str:
    if eval_result.get("case_id"):
        return str(eval_result["case_id"])
    plan_path = run_dir / "plan.json"
    if plan_path.exists():
        try:
            return load_json(plan_path).get("app_name", run_dir.parent.name)
        except Exception:
            return run_dir.parent.name
    return run_dir.parent.name


def _provider(eval_result: Dict[str, Any], run_dir: Path) -> str:
    llm = eval_result.get("llm", {}) or {}
    if llm.get("provider"):
        return str(llm.get("provider"))
    # heuristic from path
    path_str = str(run_dir)
    for name in ["deepseek", "openai", "anthropic", "mock"]:
        if name.lower() in path_str.lower():
            return name
    return "unknown"


def _load_runs(glob_pattern: str) -> List[Dict[str, Any]]:
    runs = []
    for path_str in glob.glob(glob_pattern, recursive=True):
        run_dir = Path(path_str)
        if not run_dir.is_dir():
            continue
        eval_result = _load_eval(run_dir)
        if not eval_result:
            continue
        top_errs = _top_errors(eval_result)
        warnings = _warnings_count(eval_result)
        tokens = _tokens(eval_result)
        duration = _duration_ms(eval_result)
        attempts = _attempts(eval_result)
        calls = _calls(eval_result)
        artifacts = _artifacts(run_dir)
        missing_bindings_flag = not artifacts.get("bindings")
        synthetic_err = []
        if missing_bindings_flag:
            synthetic_err.append("E_ARTIFACT_MISSING_BINDINGS")
        runs.append({
            "run_dir": str(run_dir.as_posix()),
            "case": _app_name(run_dir, eval_result),
            "provider": _provider(eval_result, run_dir),
            "core_status": _core_status(eval_result),
            "exec_status": _exec_status(eval_result),
            "overall_status": eval_result.get("overall_status"),
            "top_errors": top_errs if top_errs else synthetic_err,
            "warnings_count": warnings,
            "tokens_total": tokens,
            "calls_total": calls,
            "total_duration_ms": duration,
            "attempts_total": attempts,
            "artifacts": artifacts,
            "eval": eval_result,
            "artifact_missing_bindings": missing_bindings_flag,
            "artifact_missing_bindings_reason": "bindings file not found" if missing_bindings_flag else None,
            "synthetic_errors": synthetic_err,
        })
    return runs


def _score_success(run: Dict[str, Any]) -> float:
    warnings = run["warnings_count"] or 0
    dur = run["total_duration_ms"]
    tok = run["tokens_total"]
    score = 1000 - 10 * warnings
    if dur is not None:
        score -= 0.001 * dur
    if tok is not None:
        score -= 0.1 * tok
    return score


def _select_success(runs: List[Dict[str, Any]], require_real: bool) -> Optional[Dict[str, Any]]:
    def is_real(r):
        if not require_real:
            return True
        if r.get("provider") == "mock":
            return False
        tok = r.get("tokens_total")
        calls = r.get("calls_total")
        if (tok and tok > 0) or (calls and calls > 0):
            return True
        # provider known but tokens/calls missing -> still accept as real
        return r.get("provider") not in ("mock", "unknown")

    candidates = [r for r in runs if r["core_status"] == "PASS" and all(r["artifacts"].values()) and is_real(r)]
    if not candidates:
        return None
    best = max(candidates, key=_score_success)
    best["score"] = _score_success(best)
    best["success_type"] = "soft-success" if best["warnings_count"] else "success"
    return best


def _top_error_key(run: Dict[str, Any]) -> Optional[str]:
    if run["top_errors"]:
        return run["top_errors"][0]
    return None


def _select_failure(runs: List[Dict[str, Any]], min_repro: int, require_real: bool,
                    require_ir: bool, require_bindings: bool, exclude_codes: List[str]) -> Optional[Dict[str, Any]]:
    def is_real(r):
        if not require_real:
            return True
        if r.get("provider") == "mock":
            return False
        tok = r.get("tokens_total")
        calls = r.get("calls_total")
        if (tok and tok > 0) or (calls and calls > 0):
            return True
        return r.get("provider") not in ("mock", "unknown")

    failures = [r for r in runs if r["core_status"] == "FAIL" and r["artifacts"].get("eval") and is_real(r)]
    if require_ir:
        failures = [r for r in failures if r["artifacts"].get("ir")]
    if require_bindings:
        failures = [r for r in failures if r["artifacts"].get("bindings")]
    if not failures:
        return None
    counter = Counter()
    for r in failures:
        key = _top_error_key(r)
        if key:
            counter[key] += 1
    if not counter:
        return None
    common = [k for k, v in counter.items() if v >= min_repro and k not in exclude_codes]
    pool = [r for r in failures if _top_error_key(r) in common] if common else []
    # fallback: relax repro to 1 if none
    if not pool:
        common_relax = [k for k, v in counter.items() if v >= 1 and k not in exclude_codes]
        pool = [r for r in failures if _top_error_key(r) in common_relax]
    # final fallback: allow even excluded errors but keep bindings/real filters
    if not pool:
        pool = failures
    def score(r):
        errs = len(r["top_errors"])
        tok = r["tokens_total"] or 0
        dur = r["total_duration_ms"] or 0
        freq = counter.get(_top_error_key(r), 0)
        return freq * 100 - errs * 5 - 0.001 * dur - 0.1 * tok
    chosen = max(pool, key=score)
    chosen["top_error_repro"] = counter.get(_top_error_key(chosen), 0)
    chosen["score"] = score(chosen)
    return chosen


def _category_from_error(code: str) -> str:
    if not code:
        return "unknown"
    if code.startswith("E_SCHEMA"):
        return "schema"
    if code.startswith("E_ENDPOINT"):
        return "endpoint"
    if code.startswith("E_COVERAGE"):
        return "coverage"
    if code.startswith("E_BOUNDARY"):
        return "boundary"
    if code.startswith("E_CATALOG"):
        return "catalog"
    if code.startswith("E_CHECK"):
        return "checker"
    return "other"


def _write_case_md(path: Path, title: str, run: Dict[str, Any], extra: Dict[str, Any]):
    lines = [f"# {title}", ""]
    lines.append(f"- run_dir: `{run['run_dir']}`")
    if extra.get("bundle_dir"):
        lines.append(f"- bundle_dir: `{extra['bundle_dir']}`")
    lines.append(f"- case: {run['case']}")
    lines.append(f"- provider: {run.get('provider')}")
    lines.append(f"- core_status: {run['core_status']}  | exec_status: {run['exec_status']}")
    lines.append(f"- top_errors: {run['top_errors'] or []}")
    lines.append(f"- warnings_count: {run['warnings_count']}")
    lines.append(f"- tokens_total: {run['tokens_total']}")
    lines.append(f"- calls_total: {run.get('calls_total')}")
    lines.append(f"- total_duration_ms: {run['total_duration_ms']}")
    lines.append(f"- attempts_total: {run['attempts_total']}")
    lines.append(f"- artifacts: {run['artifacts']}")
    for k, v in extra.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Summary")
    lines.append(extra.get("summary", ""))
    # Schema bind missing fields (if any)
    missing_table = extra.get("schema_bind_missing", [])
    if missing_table:
        lines.append("")
        lines.append("## Schema Bind Missing Fields")
        lines.append("| path | missing/required | message | success_has |")
        lines.append("|---|---|---|---|")
        for row in missing_table:
            lines.append(f"| {row.get('path','')} | {row.get('missing','')} | {row.get('message','')} | {row.get('success_has','')} |")
    elif extra.get("schema_bind_note"):
        lines.append("")
        lines.append("## Schema Bind Missing Fields")
        lines.append(extra.get("schema_bind_note"))
    if run.get("artifact_missing_bindings"):
        lines.append("")
        lines.append("## Artifact Note")
        lines.append(run.get("artifact_missing_bindings_reason", "bindings file missing"))

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_compare_md(path: Path, success: Dict[str, Any], failure: Dict[str, Any]):
    lines = ["# Success vs Failure (core gate)", ""]
    lines.append("| item | success | failure |")
    lines.append("|---|---|---|")
    def fmt(run, key):
        val = run.get(key)
        return json.dumps(val) if isinstance(val, (list, dict)) else str(val)
    lines.append(f"| run_dir | `{success['run_dir']}` | `{failure['run_dir']}` |")
    lines.append(f"| bundle_dir | `{success.get('bundle_dir','')}` | `{failure.get('bundle_dir','')}` |")
    lines.append(f"| core_status | {success['core_status']} | {failure['core_status']} |")
    lines.append(f"| exec_status | {success['exec_status']} | {failure['exec_status']} |")
    lines.append(f"| top_errors | {success['top_errors']} | {failure['top_errors']} |")
    lines.append(f"| warnings_count | {success['warnings_count']} | {failure['warnings_count']} |")
    lines.append(f"| tokens_total | {success['tokens_total']} | {failure['tokens_total']} |")
    lines.append(f"| calls_total | {success.get('calls_total')} | {failure.get('calls_total')} |")
    lines.append(f"| total_duration_ms | {success['total_duration_ms']} | {failure['total_duration_ms']} |")
    lines.append(f"| attempts_total | {success['attempts_total']} | {failure['attempts_total']} |")
    lines.append(f"| artifacts | {success['artifacts']} | {failure['artifacts']} |")
    lines.append("")
    fail_cat = _category_from_error(_top_error_key(failure))
    lines.append("## Root Cause")
    lines.append(f"- Failure category: **{fail_cat}** (top error: {_top_error_key(failure)})")
    lines.append("- Suggested next steps:")
    if fail_cat == "endpoint":
        lines.append("  1) 考虑补齐 endpoint 必填或引入 stub；2) 检查 endpoint 类型/方向映射；3) 若需放宽，调整 endpoint checker 口径。")
    elif fail_cat == "schema":
        lines.append("  1) 检查 schema 必填字段；2) 评估是否可提供默认值或 normalizer；3) 确认 prompt 是否输出缺失字段。")
    elif fail_cat == "coverage":
        lines.append("  1) 明确 required/optional link；2) 放宽非关键链路覆盖；3) 增加 coverage 默认填充。")
    elif fail_cat == "boundary":
        lines.append("  1) 确认命中是否具体 URL/IP；2) 若为概念词可降级；3) 使用规则化字段代替自由描述。")
    elif fail_cat == "catalog":
        lines.append("  1) 核查未知类型；2) 考虑 alias/开放模式；3) 仅对有 profile 的组件做严格接口校验。")
    else:
        lines.append("  1) 查看 top_errors 详细信息；2) 结合 eval.checks 定位具体 checker；3) 视情况调整修复策略。")
    # Bindings diff
    diff_rows = failure.get("schema_bind_missing", [])
    lines.append("")
    lines.append("## Bindings Diff (Success vs Failure)")
    if diff_rows:
        lines.append("| path | missing/required | message | success_has |")
        lines.append("|---|---|---|---|")
        for row in diff_rows:
            lines.append(f"| {row.get('path','')} | {row.get('missing','')} | {row.get('message','')} | {row.get('success_has','')} |")
    else:
        lines.append("no E_SCHEMA_BIND details found")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _copy_bundle(src_dir: Path, bundle_dir: Path):
    ensure_dir(bundle_dir)
    to_copy = [
        "plan.json", "ir.yaml", "bindings.yaml", "eval.json", "run.log", "docker-compose.yml"
    ]
    for name in to_copy:
        src = src_dir / name
        if src.exists():
            shutil.copy2(src, bundle_dir / name)
    gen_dir = src_dir / "generated_code"
    if gen_dir.exists() and gen_dir.is_dir():
        dst_gen = bundle_dir / "generated_code"
        if dst_gen.exists():
            shutil.rmtree(dst_gen)
        shutil.copytree(gen_dir, dst_gen)


def _extract_schema_bind_missing(failure_eval: Dict[str, Any], success_bind_path: Path) -> List[Dict[str, Any]]:
    rows = []
    failures = failure_eval.get("failures_flat", []) or []
    for f in failures:
        if f.get("code") != "E_SCHEMA_BIND":
            continue
        details = f.get("details", {}) or {}
        path = details.get("path") or details.get("instance_path") or details.get("json_path") or ""
        missing = details.get("missing") or details.get("required") or ""
        msg = f.get("message", "").split("\n")[0]
        rows.append({"path": path, "missing": missing, "message": msg})
    if not rows:
        return []
    # success bindings presence check
    success_has = {}
    if success_bind_path.exists():
        try:
            success_bindings = yaml.safe_load(success_bind_path.read_text(encoding="utf-8"))
        except Exception:
            success_bindings = {}
        for row in rows:
            path = row.get("path", "")
            success_has[path] = "unknown"
            # simple path check (shallow): split by dots
            parts = [p for p in path.replace("[", ".").replace("]", "").split(".") if p]
            cur = success_bindings
            for p in parts:
                if isinstance(cur, list):
                    try:
                        idx = int(p)
                        cur = cur[idx] if idx < len(cur) else None
                    except ValueError:
                        cur = None
                elif isinstance(cur, dict):
                    cur = cur.get(p)
                else:
                    cur = None
                if cur is None:
                    break
            success_has[path] = "true" if cur is not None else "false"
    for row in rows:
        path = row.get("path", "")
        row["success_has"] = success_has.get(path, "unknown")
    return rows


def main():
    parser = argparse.ArgumentParser(description="Pick one success and one failure run (core gate) and generate reports.")
    parser.add_argument("--runs_glob", type=str, default="outputs*/**/run=*/", help="Glob to find run dirs")
    parser.add_argument("--out_dir", type=str, default="reports/cases", help="Output directory for reports")
    parser.add_argument("--min_repro", type=int, default=2, help="Min reproducibility count for failure top error")
    parser.add_argument("--require_real_llm", type=str, default="true", help="Require real LLM (non-mock) runs")
    parser.add_argument("--require_ir_for_failure", type=str, default="true", help="Failure must have IR artifact")
    parser.add_argument("--require_bindings_for_failure", type=str, default="true", help="Failure must have bindings artifact")
    parser.add_argument("--exclude_error_codes", type=str, default="E_CATALOG_COMPONENT", help="Comma-separated error codes to exclude as top_error")
    args = parser.parse_args()

    def to_bool(s: str) -> bool:
        return str(s).lower() in ("1", "true", "yes", "y")

    require_real = to_bool(args.require_real_llm)
    require_ir = to_bool(args.require_ir_for_failure)
    require_bindings = to_bool(args.require_bindings_for_failure)
    exclude_codes = [c.strip() for c in args.exclude_error_codes.split(",") if c.strip()]

    runs = _load_runs(args.runs_glob)
    ensure_dir(args.out_dir)
    (Path(args.out_dir) / "runs_index.json").write_text(json.dumps(runs, indent=2), encoding="utf-8")

    success = _select_success(runs, require_real=require_real)
    failure = _select_failure(runs, args.min_repro, require_real=require_real,
                              require_ir=require_ir, require_bindings=require_bindings,
                              exclude_codes=exclude_codes)
    fallback_no_failure_with_binding = False
    if failure is None:
        # relax bindings requirement as fallback, but mark reason
        failure = _select_failure(runs, args.min_repro, require_real=require_real,
                                  require_ir=require_ir, require_bindings=False,
                                  exclude_codes=exclude_codes)
        if failure:
            fallback_no_failure_with_binding = True

    bundles_dir = Path(args.out_dir) / "bundles"
    if success:
        s_bundle = bundles_dir / "success"
        _copy_bundle(Path(success["run_dir"]), s_bundle)
        success["bundle_dir"] = str(s_bundle.as_posix())
    if failure:
        f_bundle = bundles_dir / "failure"
        _copy_bundle(Path(failure["run_dir"]), f_bundle)
        failure["bundle_dir"] = str(f_bundle.as_posix())
        # schema bind missing table
        if success:
            success_bind_path = Path(success["bundle_dir"]) / "bindings.yaml"
        else:
            success_bind_path = Path(failure["run_dir"]) / "bindings.yaml"
        missing_table = _extract_schema_bind_missing(failure.get("eval", {}), success_bind_path)
        if failure.get("artifact_missing_bindings"):
            failure["schema_bind_note"] = "bindings file missing; schema_bind not evaluated"
        elif missing_table:
            failure["schema_bind_missing"] = missing_table
        else:
            failure["schema_bind_note"] = "no E_SCHEMA_BIND details found"

    selection = {
        "success": success,
        "failure": failure,
        "runs_scanned": len(runs),
        "filters": {
            "require_real_llm": require_real,
            "require_ir_for_failure": require_ir,
            "require_bindings_for_failure": require_bindings,
            "exclude_error_codes": exclude_codes,
        },
        "skipped_runs_summary": {
            "no_failure_binding": len([r for r in runs if r.get("core_status")=="FAIL" and not r["artifacts"].get("bindings")])
        },
        "fallback_no_failure_with_binding": fallback_no_failure_with_binding
    }
    (Path(args.out_dir) / "case_selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")

    if success:
        _write_case_md(Path(args.out_dir) / "case_success.md", "Success Case (A1, core gate)", success,
                       {"summary": "Core gate PASS，产物齐全，warnings较少"})
    if failure:
        top_err = _top_error_key(failure)
        _write_case_md(Path(args.out_dir) / "case_failure.md", "Failure Case (A1, core gate)", failure,
                       {"top_error_repro": failure.get("top_error_repro", 0),
                        "summary": f"Core gate FAIL，top_error={top_err}, repro={failure.get('top_error_repro',0)}",
                        "schema_bind_missing": failure.get("schema_bind_missing", []),
                        "schema_bind_note": failure.get("schema_bind_note")})
    if success and failure:
        _write_compare_md(Path(args.out_dir) / "case_compare.md", success, failure)
    print(f"[cases] scanned {len(runs)} runs; success={bool(success)} failure={bool(failure)}; reports in {args.out_dir}")


if __name__ == "__main__":
    main()
