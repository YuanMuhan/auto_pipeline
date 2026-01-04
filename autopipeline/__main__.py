"""CLI entry point for AutoPipeline"""

import sys
from pathlib import Path
import click

from autopipeline.runner import PipelineRunner
from autopipeline.llm.types import LLMConfig
from autopipeline.bench.aggregate import aggregate_runs
from autopipeline.bench.plots import generate_plots


@click.group()
def cli():
    """AutoPipeline - Prompt-only multi-agent pipeline for Cloud-Edge-Device development"""
    pass


@cli.command()
@click.option('--case', required=True, help='Case ID to run (e.g., DEMO-MONITORING)')
@click.option('--llm-provider', default="mock", show_default=True)
@click.option('--model', default=None, help='LLM model name')
@click.option('--temperature', default=0.0, type=float, show_default=True)
@click.option('--max-tokens', default=None, type=int)
@click.option('--cache-dir', default=".cache/llm", show_default=True)
@click.option('--no-cache', is_flag=True, default=False, help='Disable LLM cache')
@click.option('--output-root', default="outputs", show_default=True, help='Output root directory')
@click.option('--no-repair', is_flag=True, default=False, help='Disable repair loops')
@click.option('--no-catalog', is_flag=True, default=False, help='Skip catalog-based validators')
@click.option('--runtime-check', is_flag=True, default=False, help='Run docker compose config check')
@click.option('--prompt-tier', default="P0", type=click.Choice(["P0", "P1", "P2"]), show_default=True)
@click.option('--seed', default=0, type=int, show_default=True)
@click.option('--no-semantic-warnings', is_flag=True, default=False, help='Disable semantic proxy checker (warnings-only)')
def run(case: str, llm_provider: str, model: str, temperature: float, max_tokens: int,
        cache_dir: str, no_cache: bool, output_root: str, no_repair: bool, no_catalog: bool, runtime_check: bool,
        prompt_tier: str, seed: int, no_semantic_warnings: bool):
    """Run the pipeline for a specific case"""
    try:
        llm_config = LLMConfig(
            provider=llm_provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            cache_dir=cache_dir,
            cache_enabled=not no_cache,
            prompt_tier=prompt_tier,
            seed=seed
        )
        runner = PipelineRunner(
            case_id=case,
            llm_config=llm_config,
            output_root=output_root,
            enable_repair=not no_repair,
            enable_catalog=not no_catalog,
            runtime_check=runtime_check,
            enable_semantic=not no_semantic_warnings,
        )
        result = runner.run()

        click.echo("\n" + "="*60)
        click.echo("PIPELINE EXECUTION SUMMARY")
        click.echo("="*60)
        click.echo(f"Case ID: {result['case_id']}")
        click.echo(f"Status: {result['overall_status']}")
        click.echo(f"\nMetrics:")
        for key, value in result['metrics'].items():
            click.echo(f"  - {key}: {value}")

        click.echo(f"\nChecks:")
        for check_name, check_data in result['checks'].items():
            status_icon = "[PASS]" if check_data['status'] == 'PASS' else "[FAIL]"
            click.echo(f"  {status_icon} {check_name}: {check_data['status']}")

        if result['overall_status'] == 'PASS':
            click.echo("\n[SUCCESS] Pipeline completed successfully!")
            sys.exit(0)
        else:
            click.echo(f"\n[FAIL] Pipeline failed. Failed checks: {', '.join(result.get('failed_checks', []))}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"\n[ERROR] Error: {str(e)}", err=True)
        sys.exit(1)


def _discover_cases(cases_dir: Path):
    return sorted([p.name for p in cases_dir.iterdir() if p.is_dir() and (p / "user_problem.json").exists()])


@cli.command()
@click.option('--cases-dir', default="cases", show_default=True)
@click.option('--case-ids', default=None, help="Comma separated case ids; default all")
@click.option('--out-root', default="outputs_bench", show_default=True)
@click.option('--tag', default=None, help="Tag under out-root")
@click.option('--llm-provider', default="mock")
@click.option('--model', default=None)
@click.option('--temperature', default=0.0, type=float)
@click.option('--max-tokens', default=None, type=int)
@click.option('--cache-dir', default=".cache/llm")
@click.option('--no-cache', is_flag=True, default=False)
@click.option('--no-repair', is_flag=True, default=False)
@click.option('--no-catalog', is_flag=True, default=False)
@click.option('--repeat', default=1, type=int, show_default=True)
@click.option('--runtime-check', is_flag=True, default=False)
@click.option('--prompt-tier', default="P0", type=click.Choice(["P0", "P1", "P2"]), show_default=True)
@click.option('--seed', default=0, type=int, show_default=True)
@click.option('--no-semantic-warnings', is_flag=True, default=False)
def bench(cases_dir, case_ids, out_root, tag, llm_provider, model, temperature, max_tokens,
          cache_dir, no_cache, no_repair, no_catalog, repeat, runtime_check, prompt_tier, seed, no_semantic_warnings):
    """Batch run multiple cases and aggregate results."""
    base_dir = Path(".")
    cases_dir_path = base_dir / cases_dir
    selected_cases = _discover_cases(cases_dir_path) if not case_ids else [c.strip() for c in case_ids.split(",")]

    llm_config = LLMConfig(
        provider=llm_provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        cache_dir=cache_dir,
        cache_enabled=not no_cache,
        prompt_tier=prompt_tier,
        seed=seed
    )

    run_root = Path(out_root)
    if tag:
        run_root = run_root / tag

    eval_paths = []
    for rep in range(repeat):
        output_root = run_root / f"run{rep+1}"
        for cid in selected_cases:
            runner = PipelineRunner(
                case_id=cid,
                base_dir=str(base_dir),
                llm_config=llm_config,
                output_root=str(output_root),
                enable_repair=not no_repair,
                enable_catalog=not no_catalog,
                runtime_check=runtime_check,
                enable_semantic=not no_semantic_warnings,
            )
            result = runner.run()
            eval_paths.append(Path(runner.output_dir) / "eval.json")
            click.echo(f"[bench] finished {cid} rep{rep+1}: {result.get('overall_status')}")

    summary_csv, summary_error_csv = aggregate_runs(eval_paths, run_root)
    plots_dir = run_root / "plots"
    generate_plots(summary_csv, summary_error_csv, plots_dir)
    click.echo(f"[bench] summary: {summary_csv}")
    click.echo(f"[bench] summary_by_error: {summary_error_csv}")
    click.echo(f"[bench] plots in {plots_dir}")


if __name__ == '__main__':
    cli()
