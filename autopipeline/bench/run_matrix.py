"""Experiment matrix runner for AutoPipeline."""

import argparse
import itertools
from pathlib import Path
import yaml

from autopipeline.runner import PipelineRunner
from autopipeline.llm.types import LLMConfig
from autopipeline.bench.aggregate import aggregate_runs
from autopipeline.bench.plots import generate_plots


def load_experiment(config_path: Path):
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="AutoPipeline experiment matrix runner")
    parser.add_argument("--config", default="experiment.yaml", help="Path to experiment yaml")
    parser.add_argument("--out-root", default="outputs_matrix", help="Root dir for experiment outputs")
    args = parser.parse_args()

    cfg = load_experiment(Path(args.config))
    cases = cfg.get("cases", [])
    models = cfg.get("models", [])
    prompt_tiers = cfg.get("prompt_tiers", ["P0"])
    repairs = cfg.get("repair", [True])
    temperatures = cfg.get("temperatures", [0.0])
    cache_dir = cfg.get("cache_dir", ".cache/llm")
    runtime_check = cfg.get("runtime_check", False)
    no_catalog = cfg.get("no_catalog", False)
    seed = cfg.get("seed", 0)
    no_cache = cfg.get("no_cache", True)

    eval_paths = []
    for case_id, model_cfg, prompt_tier, repair, temp in itertools.product(
            cases, models, prompt_tiers, repairs, temperatures):
        provider = model_cfg.get("provider")
        model = model_cfg.get("model")
        run_dir = Path(args.out_root) / case_id / f"{provider}_{model}" / prompt_tier / \
                  ("repair" if repair else "norepair") / f"temp{temp}"
        llm_config = LLMConfig(
            provider=provider,
            model=model,
            temperature=float(temp),
            cache_dir=cache_dir,
            cache_enabled=not no_cache,
            prompt_tier=prompt_tier,
            seed=seed,
        )
        runner = PipelineRunner(
            case_id=case_id,
            llm_config=llm_config,
            output_root=str(run_dir),
            enable_repair=bool(repair),
            enable_catalog=not no_catalog,
            runtime_check=runtime_check
        )
        result = runner.run()
        eval_paths.append(Path(runner.output_dir) / "eval.json")
        print(f"[matrix] case={case_id} provider={provider} model={model} "
              f"prompt={prompt_tier} repair={repair} temp={temp} => {result.get('overall_status')}")

    # aggregate and plots
    if eval_paths:
        summary_csv, summary_error_csv = aggregate_runs(eval_paths, Path(args.out_root))
        plots_dir = Path(args.out_root) / "plots"
        try:
            generate_plots(summary_csv, summary_error_csv, plots_dir)
            print(f"[matrix] summary: {summary_csv}")
            print(f"[matrix] summary_by_error: {summary_error_csv}")
            print(f"[matrix] plots: {plots_dir}")
        except Exception as e:
            print(f"[matrix] plots skipped: {e}")


if __name__ == "__main__":
    main()
