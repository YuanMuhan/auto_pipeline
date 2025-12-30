"""Experiment matrix runner for AutoPipeline."""

import argparse
import itertools
from pathlib import Path
import yaml

from autopipeline.runner import PipelineRunner
from autopipeline.llm.types import LLMConfig


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
            cache_enabled=True,
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
        print(f"[matrix] case={case_id} provider={provider} model={model} "
              f"prompt={prompt_tier} repair={repair} temp={temp} => {result.get('overall_status')}")


if __name__ == "__main__":
    main()
