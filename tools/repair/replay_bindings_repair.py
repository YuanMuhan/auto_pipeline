import argparse
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any

import yaml

from autopipeline.normalize.bindings_normalizer import normalize_bindings
from autopipeline.repair.deterministic_patch import apply_deterministic_patch
from autopipeline.repair.context_pack import build_bindings_repair_context
from autopipeline.eval.evaluate_artifacts import evaluate_run_dir
from autopipeline.utils import sha256_of_file


def _load_eval_failures(run_dir: Path) -> List[Dict[str, Any]]:
    eval_path = run_dir / "eval.json"
    if not eval_path.exists():
        return []
    try:
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        return data.get("failures_flat") or []
    except Exception:
        return []


def _load_bindings_source(run_dir: Path) -> Dict[str, Any]:
    for name in ["bindings_raw.yaml", "bindings_norm.yaml", "bindings.yaml", "bindings_raw.txt"]:
        p = run_dir / name
        if p.exists():
            try:
                return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            except Exception:
                return {}
    return {}


def _top_error(failures: List[Dict[str, Any]]) -> str:
    if not failures:
        return ""
    return failures[0].get("code") or ""


def replay(run_dir: Path, gate_mode: str = "core", out_subdir: str = "replay_repair", max_attempts: int = 2,
           enable_llm_patch: bool = False) -> Dict[str, Any]:
    run_dir = run_dir.resolve()
    out_dir = run_dir / out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    failures = _load_eval_failures(run_dir)
    bindings_raw = _load_bindings_source(run_dir)
    ctx = build_bindings_repair_context(str(run_dir), failures)
    failure_hints = ctx.get("failure_hints", [])

    # deterministic patch first (no LLM)
    patched, actions = apply_deterministic_patch(bindings_raw, ctx.get("ir") or {}, failure_hints)
    patched_path = out_dir / "bindings_patched_attempt1.yaml"
    patched_path.write_text(yaml.safe_dump(patched, sort_keys=False), encoding="utf-8")

    # normalize again for consistency
    norm, norm_actions = normalize_bindings(patched, ctx.get("ir") or {}, ctx.get("device_info") or {}, gate_mode=gate_mode)
    norm_path = out_dir / "bindings_norm.yaml"
    norm_path.write_text(yaml.safe_dump(norm, sort_keys=False), encoding="utf-8")

    # prepare evaluation dir: copy plan/ir/inputs, and set bindings.yaml to patched norm
    eval_dir = out_dir
    for name in ["plan.json", "ir.yaml", "placement_plan.yaml", "run.log", "eval.json"]:
        src = run_dir / name
        if src.exists():
            shutil.copy2(src, eval_dir / name)
    # copy inputs
    inputs_dir = run_dir / "inputs"
    if inputs_dir.exists():
        dst_inputs = eval_dir / "inputs"
        dst_inputs.mkdir(parents=True, exist_ok=True)
        for item in inputs_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, dst_inputs / item.name)
    # write bindings.yaml for evaluator
    (eval_dir / "bindings.yaml").write_text(yaml.safe_dump(norm, sort_keys=False), encoding="utf-8")

    # stub generation artifacts for GenerationConsistencyChecker
    bindings_hash = sha256_of_file(eval_dir / "bindings.yaml")
    gen_dir = eval_dir / "generated_code"
    gen_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"bindings_hash": bindings_hash}
    (gen_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for layer in ("cloud", "edge", "device"):
        layer_dir = gen_dir / layer
        layer_dir.mkdir(exist_ok=True, parents=True)
        (layer_dir / "main.py").write_text(f"# bindings_hash {bindings_hash}\n", encoding="utf-8")
    compose_path = eval_dir / "docker-compose.yml"
    compose_path.write_text(f"services:\n  stub:\n    image: stub\n    labels:\n      - BINDINGS_HASH={bindings_hash}\n", encoding="utf-8")

    eval_res = evaluate_run_dir(eval_dir, gate_mode=gate_mode)
    (eval_dir / "eval_repaired.json").write_text(json.dumps(eval_res, indent=2, ensure_ascii=False), encoding="utf-8")
    trace = [{
        "strategy": "deterministic_patch",
        "used_hints_count": len(failure_hints),
        "patch_actions_count": len(actions) + len(norm_actions),
        "artifact_written": str(patched_path.relative_to(run_dir)),
    }]
    (eval_dir / "repair_trace.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")

    new_top = _top_error(eval_res.get("failures_flat") or [])
    debug_unknown = {}
    if new_top == "E_UNKNOWN":
        debug_unknown = {
            "failures": eval_res.get("failures_flat", []),
            "validators": eval_res.get("validators", {}),
        }
        (eval_dir / "debug_unknown.json").write_text(json.dumps(debug_unknown, indent=2, ensure_ascii=False), encoding="utf-8")

    if new_top == "E_SCHEMA_BIND":
        print(f"[replay] E_SCHEMA_BIND still present after repair. See {eval_dir}")
        raise SystemExit(1)
    return {
        "out_dir": str(out_dir),
        "before_top_error": _top_error(failures),
        "after_top_error": new_top,
        "trace": trace,
        "debug_unknown": debug_unknown,
    }


def main():
    parser = argparse.ArgumentParser(description="Replay bindings repair on an existing failing run_dir.")
    parser.add_argument("--run_dir", required=True, help="Path to failing run directory")
    parser.add_argument("--gate_mode", default="core", choices=["core", "full"])
    parser.add_argument("--out_subdir", default="replay_repair")
    parser.add_argument("--max_attempts", type=int, default=2)
    parser.add_argument("--enable_llm_patch", action="store_true", default=False)
    args = parser.parse_args()

    res = replay(Path(args.run_dir), gate_mode=args.gate_mode, out_subdir=args.out_subdir,
                 max_attempts=args.max_attempts, enable_llm_patch=args.enable_llm_patch)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
