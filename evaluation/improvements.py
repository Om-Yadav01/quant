import os
import sys
import pandas as pd
import numpy as np
 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR       = os.path.join(_PROJECT_ROOT, "results", "csv")
 
METRICS = [
    ("avg_completion_time", "Avg Completion Time",  True),
    ("p95_latency",         "P95 Latency",          True),
    ("makespan",            "Makespan",              True),
    ("slr",                 "SLR",                   True),
    ("load_variance",       "Load Variance",         True),
    ("failure_rate",        "Failure Rate",          True),
    ("throughput",          "Throughput",            False),   # higher is better
]
 
BASELINES   = ["Round Robin", "Least Loaded", "MECT"]
OPTIMIZERS  = ["Policy-GA", "Policy-PSO", "Policy-DE", "Policy-Hybrid CCE"]
OPT_LABELS  = ["GA", "PSO", "DE", "Hybrid CCE"]
 
 
def compute_improvement(baseline_val: float, optimizer_val: float,
                        lower_is_better: bool) -> float:
    if abs(baseline_val) < 1e-12:
        return 0.0
    if lower_is_better:
        return (baseline_val - optimizer_val) / abs(baseline_val) * 100
    else:
        return (optimizer_val - baseline_val) / abs(baseline_val) * 100
 
 
def generate_improvement_matrix(comparison_csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(comparison_csv_path, index_col=0)
 
    available = df.index.tolist()
    missing   = [s for s in BASELINES + OPTIMIZERS if s not in available]
    if missing:
        print(f"[WARNING] Missing rows in comparison CSV: {missing}")
        print(f"          Available: {available}")
 
    rows = []
    for opt_label, opt_key in zip(OPT_LABELS, OPTIMIZERS):
        if opt_key not in df.index:
            continue
 
        row = {"Optimizer": opt_label}
 
        for baseline in BASELINES:
            if baseline not in df.index:
                continue
 
            for col, display, lower_is_better in METRICS:
                if col not in df.columns:
                    continue
 
                baseline_val  = float(df.loc[baseline,  col])
                optimizer_val = float(df.loc[opt_key,   col])
                improv        = compute_improvement(
                    baseline_val, optimizer_val, lower_is_better
                )
 
                baseline_short = (baseline
                                  .replace("Round Robin", "RR")
                                  .replace("Least Loaded", "LL")
                                  .replace("MECT", "MECT"))
                metric_short   = (display
                                  .replace("Avg Completion Time", "AvgCT")
                                  .replace("P95 Latency", "P95")
                                  .replace("Load Variance", "LoadVar")
                                  .replace("Failure Rate", "FailRate")
                                  .replace(" ", ""))
 
                col_name       = f"vs_{baseline_short}_{metric_short}_%"
                row[col_name]  = round(improv, 4)
 
                if baseline == BASELINES[0]:
                    row[f"raw_{metric_short}"] = round(optimizer_val, 6)
 
        rows.append(row)
 
    result_df = pd.DataFrame(rows).set_index("Optimizer")
    return result_df
 
 
def generate_summary_table(comparison_csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(comparison_csv_path, index_col=0)
 
    all_schedulers = BASELINES + OPTIMIZERS
    all_schedulers = [s for s in all_schedulers if s in df.index]
 
    mect_row = df.loc["MECT"]
 
    rows = []
    for sched in all_schedulers:
        row = {"Scheduler": sched.replace("Policy-", "")}
        for col, display, lower_is_better in METRICS:
            if col not in df.columns:
                continue
            val   = float(df.loc[sched, col])
            mect  = float(mect_row[col])
            improv = compute_improvement(mect, val, lower_is_better)
 
            metric_short = (display
                            .replace("Avg Completion Time", "AvgCT")
                            .replace("P95 Latency", "P95")
                            .replace("Load Variance", "LoadVar")
                            .replace("Failure Rate", "FailRate")
                            .replace(" ", ""))
 
            row[metric_short]              = round(val,    4)
            row[f"{metric_short}_vs_MECT%"] = round(improv, 2)
 
        rows.append(row)
 
    return pd.DataFrame(rows).set_index("Scheduler")
 
 
def print_improvement_report(matrix_df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE IMPROVEMENT MATRIX")
    print("  Positive % = optimizer outperforms baseline on that metric")
    print("=" * 80)
 
    baselines_short = ["RR", "LL", "MECT"]
 
    for metric_col, display, lower_is_better in METRICS:
        metric_short = (display
                        .replace("Avg Completion Time", "AvgCT")
                        .replace("P95 Latency", "P95")
                        .replace("Load Variance", "LoadVar")
                        .replace("Failure Rate", "FailRate")
                        .replace(" ", ""))
 
        direction = "↓ lower=better" if lower_is_better else "↑ higher=better"
        print(f"\n  {display} ({direction})")
        print(f"  {'Optimizer':<14}" + "".join(f"  vs {b:>6}" for b in baselines_short))
        print(f"  {'─'*50}")
 
        for opt in matrix_df.index:
            vals = []
            for b in baselines_short:
                col = f"vs_{b}_{metric_short}_%"
                if col in matrix_df.columns:
                    v = matrix_df.loc[opt, col]
                    vals.append(f"{v:>+8.2f}%")
                else:
                    vals.append(f"{'N/A':>9}")
            print(f"  {opt:<14}" + "  ".join(vals))
 
 
def main():
    comparison_csv = os.path.join(CSV_DIR, "phase2_full_comparison.csv")
 
    if not os.path.exists(comparison_csv):
        print(f"[ERROR] File not found: {comparison_csv}")
        print("  Run hybrid_experiment.py first to generate the comparison CSV.")
        return
 
    print(f"[INFO] Loading: {comparison_csv}")
 
    matrix_df = generate_improvement_matrix(comparison_csv)
    matrix_path = os.path.join(CSV_DIR, "final_improvement_matrix.csv")
    matrix_df.to_csv(matrix_path)
 
    summary_df = generate_summary_table(comparison_csv)
    summary_path = os.path.join(CSV_DIR, "final_summary_table.csv")
    summary_df.to_csv(summary_path)
 
    print_improvement_report(matrix_df)
 
    print("\n" + "=" * 80)
    print("  SUMMARY TABLE (raw values + % improvement over MECT)")
    print("=" * 80)
    print(summary_df.to_string())
 
    print("    phase2_improvement_matrix.csv  — full matrix (all baselines)")
    print("    phase2_summary_table.csv       — clean paper-ready table")
 
 
if __name__ == "__main__":
    main()

