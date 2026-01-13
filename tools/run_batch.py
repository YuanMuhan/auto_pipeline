import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path


def find_latest_run(case_dir: Path) -> Path | None:
    runs = [p for p in case_dir.glob("run=*") if p.is_dir()]
    if not runs:
        return None
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0]


def main():
    parser = argparse.ArgumentParser(description="Batch run autopipeline with retry and optional alias copies.")
    parser.add_argument("--case", default="DEMO-MONITORING")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--prompt-tier", default="P0")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--output-root", default="outputs_batch_openai")
    parser.add_argument("--alias-root", default="outputs_batch_openai_seq")
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--sleep", type=float, default=1.0, help="seconds between runs")
    parser.add_argument("--extra-args", default="", help="extra args string, e.g., '--no-cache'")
    parser.add_argument("--continue-on-fail", action="store_true", help="do not stop batch when a run keeps failing")
    args = parser.parse_args()

    base_cmd = [
        "python", "-m", "autopipeline", "run",
        "--case", args.case,
        "--llm-provider", args.provider,
        "--model", args.model,
        "--prompt-tier", args.prompt_tier,
        "--temperature", str(args.temperature),
        "--output-root", args.output_root
    ]
    if args.extra_args:
        base_cmd.extend(args.extra_args.split())

    alias_root = Path(args.alias_root) / args.case
    alias_root.mkdir(parents=True, exist_ok=True)
    case_dir = Path(args.output_root) / args.case
    case_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, args.count + 1):
        print(f"=== batch run {i}/{args.count} ===")
        ok = False
        for r in range(1, args.retries + 1):
            code = subprocess.call(base_cmd)
            if code == 0:
                ok = True
                break
            print(f"  retry {r}/{args.retries} failed with code {code}, retrying...")
            time.sleep(args.sleep)
        if not ok:
            print(f"!! run {i} failed after {args.retries} retries")
            if not args.continue_on_fail:
                print("!! stopping batch (use --continue-on-fail to keep going)")
                break
            else:
                continue

        latest = find_latest_run(case_dir)
        if latest:
            alias_dir = alias_root / f"run{i:02d}"
            if alias_dir.exists():
                shutil.rmtree(alias_dir, ignore_errors=True)
            shutil.copytree(latest, alias_dir)
            print(f"  copied {latest.name} -> {alias_dir}")

        time.sleep(args.sleep)


if __name__ == "__main__":
    main()
