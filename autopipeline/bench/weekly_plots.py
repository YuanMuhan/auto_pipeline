"""Weekly plotting utility for bench outputs (summary.csv / summary_by_error.csv)."""

import argparse
import ast
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def _require_libs():
    try:
        import pandas as pd  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise SystemExit(f"pandas not available: {e}. Please pip install pandas") from e
    try:
        import matplotlib.pyplot as plt  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise SystemExit(f"matplotlib not available: {e}. Please pip install matplotlib") from e


def _find_latest(path: Path, name: str) -> Optional[Path]:
    candidates = list(path.rglob(name))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _load_summary(args) -> Tuple["pd.DataFrame", Optional["pd.DataFrame"], Path]:
    import pandas as pd

    summary_path = Path(args.summary) if args.summary else None
    if summary_path and not summary_path.exists():
        raise SystemExit(f"summary.csv not found: {summary_path}")
    if summary_path is None:
        root = Path(args.matrix_root)
        summary_path = _find_latest(root, "summary.csv")
        if not summary_path:
            raise SystemExit(f"No summary.csv found under {root}")
    summary_df = pd.read_csv(summary_path)

    summary_err_path = Path(args.summary_by_error) if args.summary_by_error else None
    if summary_err_path and summary_err_path.exists():
        err_df = pd.read_csv(summary_err_path)
    else:
        cand = _find_latest(summary_path.parent, "summary_by_error.csv") if summary_path else None
        err_df = pd.read_csv(cand) if cand and cand.exists() else None

    return summary_df, err_df, summary_path


def _normalize_repair(val: Any) -> str:
    if isinstance(val, str):
        if "on" in val.lower() or val.lower() in ("true", "yes"):
            return "on"
        return "off"
    if isinstance(val, bool):
        return "on" if val else "off"
    return "off"


def _add_compat_cols(df):
    # status_static
    if "status_static" not in df and "status" in df:
        df["status_static"] = df["status"]
    # attempts_total
    if "attempts_total" not in df and "total_attempts" in df:
        df["attempts_total"] = df["total_attempts"]
    if "total_duration_ms" not in df and "duration_ms_total" in df:
        df["total_duration_ms"] = df["duration_ms_total"]
    # repair
    if "repair_enabled" in df:
        df["repair_flag"] = df["repair_enabled"].apply(_normalize_repair)
    elif "repair" in df:
        df["repair_flag"] = df["repair"].apply(_normalize_repair)
    else:
        df["repair_flag"] = "on"
    return df


def _box_or_bar(ax, data, labels, min_samples_boxplot: int, ylabel: str):
    import numpy as np

    if all(len(d) < min_samples_boxplot for d in data):
        means = [np.mean(d) if len(d) else 0 for d in data]
        ax.bar(labels, means)
    else:
        ax.boxplot(data, labels=labels)
    ax.set_ylabel(ylabel)


def _fig1_pass_rate(df, out_dir: Path, min_samples_boxplot: int):
    import matplotlib.pyplot as plt
    import numpy as np
    fig_paths = []
    for case_id, g in df.groupby("case_id"):
        tiers = sorted(g["prompt_tier"].dropna().unique())
        repair_opts = sorted(g["repair_flag"].dropna().unique())
        data = np.zeros((len(tiers), len(repair_opts)))
        counts = np.zeros_like(data)
        for i, t in enumerate(tiers):
            for j, r in enumerate(repair_opts):
                subset = g[(g["prompt_tier"] == t) & (g["repair_flag"] == r)]
                counts[i, j] = len(subset)
                if len(subset) == 0:
                    data[i, j] = 0
                else:
                    data[i, j] = (subset["status_static"].str.upper() == "PASS").mean()
        x = np.arange(len(tiers))
        width = 0.35 if len(repair_opts) == 2 else 0.25
        fig, ax = plt.subplots()
        for idx, r in enumerate(repair_opts):
            ax.bar(x + (idx - len(repair_opts)/2)*width + width/2, data[:, idx], width, label=f"repair={r}")
        ax.set_xticks(x)
        ax.set_xticklabels(tiers)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Static PASS Rate")
        ax.set_title(f"Static PASS Rate - {case_id}")
        ax.legend()
        ax.text(0.01, 0.01, f"samples={int(counts.sum())}", transform=ax.transAxes)
        path = out_dir / f"fig1_static_pass_rate__{case_id}.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        fig_paths.append(path)
    return fig_paths


def _fig2_attempts(df, out_dir: Path, min_samples_boxplot: int):
    import matplotlib.pyplot as plt

    fig_paths = []
    for case_id, g in df.groupby("case_id"):
        labels = []
        data = []
        for t in sorted(g["prompt_tier"].dropna().unique()):
            for r in sorted(g["repair_flag"].dropna().unique()):
                subset = g[(g["prompt_tier"] == t) & (g["repair_flag"] == r)]
                labels.append(f"{t}-repair={r}")
                data.append(subset["attempts_total"].dropna().tolist())
        fig, ax = plt.subplots()
        _box_or_bar(ax, data, labels, min_samples_boxplot, "Attempts (total)")
        ax.set_title(f"Attempts Distribution - {case_id}")
        fig.tight_layout()
        path = out_dir / f"fig2_attempts_distribution__{case_id}.png"
        fig.savefig(path)
        plt.close(fig)
        fig_paths.append(path)
    return fig_paths


def _fig3_semantic(df, out_dir: Path, min_samples_boxplot: int, only_static_pass: bool):
    import matplotlib.pyplot as plt

    fig_paths = []
    df_use = df
    if only_static_pass:
        df_use = df[df["status_static"].str.upper() == "PASS"]
    if "semantic_warning_count" not in df_use:
        return fig_paths
    for case_id, g in df_use.groupby("case_id"):
        labels = []
        data = []
        for t in sorted(g["prompt_tier"].dropna().unique()):
            for r in sorted(g["repair_flag"].dropna().unique()):
                subset = g[(g["prompt_tier"] == t) & (g["repair_flag"] == r)]
                labels.append(f"{t}-repair={r}")
                data.append(subset["semantic_warning_count"].dropna().tolist())
        if not any(data):
            continue
        fig, ax = plt.subplots()
        _box_or_bar(ax, data, labels, min_samples_boxplot, "Semantic Warnings")
        ax.set_title(f"Semantic Warning Count - {case_id}")
        fig.tight_layout()
        path = out_dir / f"fig3_semantic_warning_count__{case_id}.png"
        fig.savefig(path)
        plt.close(fig)
        fig_paths.append(path)
    return fig_paths


def _fig4_errors(df: "pd.DataFrame", err_df: Optional["pd.DataFrame"], out_dir: Path, topk: int):
    import matplotlib.pyplot as plt

    if err_df is None and "error_code_top1" not in df:
        return []
    counter = Counter()
    if err_df is not None and "code" in err_df.columns:
        for _, row in err_df.iterrows():
            counter[row["code"]] += row.get("count", 0) or row.get("rate", 0)
    else:
        fail = df[df["status_static"].str.upper() == "FAIL"]
        counter.update(fail["error_code_top1"].dropna().tolist())
    if not counter:
        return []
    top_items = counter.most_common(topk)
    labels, counts = zip(*top_items)
    fig, ax = plt.subplots()
    ax.bar(labels, counts)
    ax.set_ylabel("Count")
    ax.set_title("Top Error Codes")
    fig.tight_layout()
    path = out_dir / "fig4_error_distribution_topk.png"
    fig.savefig(path)
    plt.close(fig)
    return [path]


def _fig5_cost(df, out_dir: Path, min_samples_boxplot: int):
    import matplotlib.pyplot as plt

    fig_paths = []
    # tokens
    if "tokens_total" in df.columns and df["tokens_total"].notna().any():
        labels = []
        data = []
        for t in sorted(df["prompt_tier"].dropna().unique()):
            for r in sorted(df["repair_flag"].dropna().unique()):
                subset = df[(df["prompt_tier"] == t) & (df["repair_flag"] == r)]
                labels.append(f"{t}-repair={r}")
                data.append(subset["tokens_total"].dropna().tolist())
        if any(data):
            fig, ax = plt.subplots()
            _box_or_bar(ax, data, labels, min_samples_boxplot, "Tokens")
            ax.set_title("Tokens Total")
            fig.tight_layout()
            path = out_dir / "fig5_cost_tokens.png"
            fig.savefig(path)
            plt.close(fig)
            fig_paths.append(path)
    # time
    if "total_duration_ms" in df.columns and df["total_duration_ms"].notna().any():
        labels = []
        data = []
        for t in sorted(df["prompt_tier"].dropna().unique()):
            for r in sorted(df["repair_flag"].dropna().unique()):
                subset = df[(df["prompt_tier"] == t) & (df["repair_flag"] == r)]
                labels.append(f"{t}-repair={r}")
                data.append(subset["total_duration_ms"].dropna().tolist())
        if any(data):
            fig, ax = plt.subplots()
            _box_or_bar(ax, data, labels, min_samples_boxplot, "Duration (ms)")
            ax.set_title("Total Duration")
            fig.tight_layout()
            path = out_dir / "fig5_cost_time_ms.png"
            fig.savefig(path)
            plt.close(fig)
            fig_paths.append(path)
    return fig_paths


def _write_md(fig_paths: Dict[str, List[Path]], out_dir: Path, df):
    lines = ["# Weekly Figures", ""]
    for title, paths in fig_paths.items():
        if not paths:
            continue
        lines.append(f"## {title}")
        for p in paths:
            rel = p.relative_to(out_dir)
            lines.append(f"![{p.name}]({rel.as_posix()})")
        if title.lower().startswith("fig1"):
            lines.append("- Static PASS 口径；bar=repair on/off；x=prompt_tier（每 case 各一张）")
        if title.lower().startswith("fig2"):
            lines.append("- attempts_total 分布；样本少则均值柱状")
        if title.lower().startswith("fig3"):
            lines.append("- 仅统计 static PASS 的语义警告数（warnings-only）")
        if title.lower().startswith("fig4"):
            lines.append("- TopK error codes（count），无 summary_by_error 时从 FAIL runs 的 error_code_top1 统计")
        if title.lower().startswith("fig5"):
            lines.append("- tokens_total/total_duration_ms 分布（缺列则跳过）")
        lines.append("")
    # 小表格（均值）
    import pandas as pd
    lines.append("## Summary (mean by prompt_tier x repair)")
    if "status_static" in df:
        def _group_mean(col):
            if col not in df:
                return None
            g = df.groupby(["prompt_tier", "repair_flag"])[col].mean()
            return g.unstack().round(3)
        pass_rate = df.groupby(["prompt_tier", "repair_flag"])["status_static"].apply(lambda s: (s.str.upper() == "PASS").mean()).unstack().round(3)
        tbl = {
            "pass_rate_static": pass_rate,
            "attempts_mean": _group_mean("attempts_total"),
            "tokens_mean": _group_mean("tokens_total"),
            "semantic_warnings_mean": _group_mean("semantic_warning_count"),
        }
        for name, t in tbl.items():
            if t is None:
                continue
            lines.append(f"### {name}")
            try:
                lines.append(t.to_markdown())
            except Exception:
                lines.append(t.to_string())
            lines.append("")
    out_path = out_dir / "WEEKLY_FIGURES.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    _require_libs()
    import pandas as pd

    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix-root", default="outputs_matrix", help="Root dir containing summary.csv")
    parser.add_argument("--summary", default=None, help="Explicit summary.csv path")
    parser.add_argument("--summary-by-error", default=None, help="Explicit summary_by_error.csv path")
    parser.add_argument("--out-dir", default=None, help="Output dir for figures and md")
    parser.add_argument("--case-ids", default=None, help="Comma separated case ids to filter")
    parser.add_argument("--only-static-pass-for-semantic", action="store_true", default=True)
    parser.add_argument("--topk-errors", type=int, default=5)
    parser.add_argument("--min-samples-boxplot", type=int, default=5)
    args = parser.parse_args()

    summary_df, err_df, summary_path = _load_summary(args)
    summary_df = _add_compat_cols(summary_df)
    if args.case_ids:
        ids = [c.strip() for c in args.case_ids.split(",")]
        summary_df = summary_df[summary_df["case_id"].isin(ids)]

    out_dir = Path(args.out_dir) if args.out_dir else summary_path.parent / "weekly_plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    # parse attempts_by_stage string safely (optional)
    if "attempts_by_stage" in summary_df.columns:
        def _safe_stage(x):
            try:
                if isinstance(x, str):
                    return ast.literal_eval(x)
            except Exception:
                return {}
            return x if isinstance(x, dict) else {}
        summary_df["attempts_by_stage_dict"] = summary_df["attempts_by_stage"].apply(_safe_stage)

    info = f"Loaded summary rows={len(summary_df)}, cases={summary_df['case_id'].nunique()}, tiers={summary_df['prompt_tier'].nunique()}, repairs={summary_df['repair_flag'].nunique()}"
    print(info)

    fig_paths: Dict[str, List[Path]] = {}
    fig_paths["Fig1 Static PASS Rate"] = _fig1_pass_rate(summary_df, out_dir, args.min_samples_boxplot)
    fig_paths["Fig2 Attempts Distribution"] = _fig2_attempts(summary_df, out_dir, args.min_samples_boxplot)
    fig_paths["Fig3 Semantic Warning Count"] = _fig3_semantic(summary_df, out_dir, args.min_samples_boxplot, args.only_static_pass_for_semantic)
    fig_paths["Fig4 Error Distribution"] = _fig4_errors(summary_df, err_df, out_dir, args.topk_errors)
    fig_paths["Fig5 Cost (tokens/time)"] = _fig5_cost(summary_df, out_dir, args.min_samples_boxplot)

    md_path = _write_md(fig_paths, out_dir, summary_df)
    print(f"Figures written to {out_dir}, index: {md_path}")


if __name__ == "__main__":
    main()
