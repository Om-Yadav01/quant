import numpy as np
import pandas as pd


def compute_metrics(df: pd.DataFrame, tasks_per_node: list,nodes: list = None) -> dict:
    ct   = df["completion_time"].dropna()
    span = df["arrival_time"].max() - df["arrival_time"].min()
    throughput = len(df) / span if span > 0 else 0.0
    
    makespan = float(ct.max())

    if nodes is not None:
        max_speed    = max(n["processing_speed"] for n in nodes)
        critical_sum = float((df["workload_size"] / max_speed).sum())
        slr = makespan / critical_sum if critical_sum > 0 else 0.0
    else:
        slr = None
 
    return {
        "avg_completion_time": float(ct.mean()),
        "p95_latency":         float(np.percentile(ct, 95)),
        "load_variance":       float(np.var(tasks_per_node)),
        "failure_rate":        float(df["failed"].mean()),
        "throughput":          float(throughput),
        "makespan":            makespan,
        "slr":                 slr,
    }


def build_metrics_table(all_metrics: dict) -> pd.DataFrame:
    return pd.DataFrame(all_metrics).T.round(4)


