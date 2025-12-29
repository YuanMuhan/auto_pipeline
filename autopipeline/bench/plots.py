"""Plot generation for bench summaries."""

from pathlib import Path
import csv
from collections import defaultdict
from typing import Dict, List

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - optional dependency
    plt = None

from autopipeline.utils import ensure_dir


def _load_summary(summary_csv: Path) -> List[Dict[str, str]]:
    rows = []
    with open(summary_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def generate_plots(summary_csv: Path, summary_error_csv: Path, out_dir: Path):
    if plt is None:
        print("[plots] matplotlib not installed; skipping plot generation")
        return
    ensure_dir(str(out_dir))
    rows = _load_summary(summary_csv) if summary_csv.exists() else []

    # Pass rate by case
    pass_rate: Dict[str, List[int]] = defaultdict(list)
    for r in rows:
        case = r.get("case_id", "UNKNOWN")
        pass_rate[case].append(int(r.get("pass", 0)))
    cases = list(pass_rate.keys())
    rates = [sum(pass_rate[c]) / len(pass_rate[c]) if pass_rate[c] else 0 for c in cases]
    plt.figure()
    plt.bar(cases, rates, color="seagreen")
    plt.ylabel("Pass Rate")
    plt.ylim(0, 1.0)
    plt.title("Pass Rate by Case")
    plt.tight_layout()
    plt.savefig(out_dir / "pass_rate_by_case.png")
    plt.close()

    # Failure code histogram
    error_counts = defaultdict(int)
    if summary_error_csv.exists():
        with open(summary_error_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                error_counts[row["error_code"]] = int(row["count"])
    plt.figure()
    if error_counts:
        plt.bar(error_counts.keys(), error_counts.values(), color="salmon")
        plt.ylabel("Count")
        plt.title("Failure Code Histogram")
        plt.xticks(rotation=45, ha="right")
    else:
        plt.text(0.5, 0.5, "No failures", ha="center", va="center")
        plt.xticks([])
        plt.yticks([])
    plt.tight_layout()
    plt.savefig(out_dir / "failure_code_hist.png")
    plt.close()

    # Repair attempts distribution (max of ir/bindings)
    attempts = []
    for r in rows:
        ir_att = int(r.get("ir_attempts") or 0)
        bind_att = int(r.get("bindings_attempts") or 0)
        attempts.append(max(ir_att, bind_att))
    plt.figure()
    if attempts:
        plt.hist(attempts, bins=range(1, max(attempts) + 2), color="steelblue", align="left", rwidth=0.8)
        plt.xlabel("Max Attempts (IR/Bindings)")
        plt.ylabel("Runs")
        plt.title("Repair Attempts Distribution")
    else:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.xticks([])
        plt.yticks([])
    plt.tight_layout()
    plt.savefig(out_dir / "repair_attempts_dist.png")
    plt.close()
