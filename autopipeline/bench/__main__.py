"""Bench CLI for running multiple cases."""

import argparse
from pathlib import Path
from typing import List

from autopipeline.runner import PipelineRunner
from autopipeline.llm.types import LLMConfig
from autopipeline.bench.aggregate import aggregate_runs
from autopipeline.bench.plots import generate_plots


def discover_cases(cases_dir: Path) -> List[str]:
    case_ids = []
    for entry in cases_dir.iterdir():
        if entry.is_dir() and (entry / "user_problem.json").exists():
            case_ids.append(entry.name)
    return sorted(case_ids)


def main():
    parser = argparse.ArgumentParser(description="AutoPipeline Bench Runner")
    parser.add_argument("--cases-dir", default="cases")
    parser.add_argument("--case-ids", default=None, help="Comma separated case ids; default=all in cases-dir")
    parser.add_argument("--out-root", default="outputs_bench")
    parser.add_argument("--tag", default=None, help="Tag for this bench run")
    parser.add_argument("--llm-provider", default="mock")
    parser.add_argument("--model", default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--cache-dir", default=".cache/llm")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--no-repair", action="store_true", help="Disable repair loops (single attempt)")
    parser.add_argument("--no-catalog", action="store_true", help="Skip catalog-based validators")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat each case N times")
    parser.add_argument("--runtime-check", action="store_true", help="Run docker compose config during bench")
    parser.add_argument("--base-dir", default=".")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    cases_dir = base_dir / args.cases_dir
    if args.case_ids:
        case_ids = [c.strip() for c in args.case_ids.split(",") if c.strip()]
    else:
        case_ids = discover_cases(cases_dir)

    llm_config = LLMConfig(
        provider=args.llm_provider,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        cache_dir=args.cache_dir,
        cache_enabled=not args.no_cache
    )

    run_root = Path(args.out_root)
    if args.tag:
        run_root = run_root / args.tag

    eval_paths = []
    for rep in range(args.repeat):
        output_root = run_root / f"run{rep+1}"
        for case_id in case_ids:
            runner = PipelineRunner(
                case_id=case_id,
                base_dir=str(base_dir),
                llm_config=llm_config,
                output_root=str(output_root),
                enable_repair=not args.no_repair,
                enable_catalog=not args.no_catalog,
                runtime_check=args.runtime_check
            )
            result = runner.run()
            eval_paths.append(Path(runner.output_dir) / "eval.json")
            print(f"[bench] finished {case_id} rep{rep+1}: {result.get('overall_status')}")

    summary_dir = run_root
    summary_csv, summary_error_csv = aggregate_runs(eval_paths, summary_dir)
    plots_dir = summary_dir / "plots"
    generate_plots(summary_csv, summary_error_csv, plots_dir)
    print(f"[bench] summary written to {summary_csv} and {summary_error_csv}")
    print(f"[bench] plots written to {plots_dir}")


if __name__ == "__main__":
    main()
