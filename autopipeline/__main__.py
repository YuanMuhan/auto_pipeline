"""CLI entry point for AutoPipeline"""

import sys
import click
from autopipeline.runner import PipelineRunner
from autopipeline.llm.types import LLMConfig


@click.group()
def cli():
    """AutoPipeline - Prompt-only multi-agent pipeline for Cloud-Edge-Device development"""
    pass


@cli.command()
@click.option('--case', required=True, help='Case ID to run (e.g., demo001)')
@click.option('--llm-provider', default="mock", show_default=True)
@click.option('--model', default=None, help='LLM model name')
@click.option('--temperature', default=0.0, type=float, show_default=True)
@click.option('--max-tokens', default=None, type=int)
@click.option('--cache-dir', default=".cache/llm", show_default=True)
@click.option('--no-cache', is_flag=True, default=False, help='Disable LLM cache')
def run(case: str, llm_provider: str, model: str, temperature: float, max_tokens: int,
        cache_dir: str, no_cache: bool):
    """Run the pipeline for a specific case"""
    try:
        llm_config = LLMConfig(
            provider=llm_provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            cache_dir=cache_dir,
            cache_enabled=not no_cache
        )
        runner = PipelineRunner(case_id=case, llm_config=llm_config)
        result = runner.run()

        # Print summary
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


if __name__ == '__main__':
    cli()
