"""CLI entry point for AutoPipeline"""

import sys
import click
from autopipeline.runner import PipelineRunner


@click.group()
def cli():
    """AutoPipeline - Prompt-only multi-agent pipeline for Cloud-Edge-Device development"""
    pass


@cli.command()
@click.option('--case', required=True, help='Case ID to run (e.g., demo001)')
def run(case: str):
    """Run the pipeline for a specific case"""
    try:
        runner = PipelineRunner(case_id=case)
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
