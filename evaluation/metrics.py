import numpy as np
import pandas as pd


def _finish_times(df: pd.DataFrame) -> pd.Series:
    if "finish_time" in df.columns:
        return df["finish_time"].dropna()
    return (df["arrival_time"] + df["completion_time"]).dropna()


def _parallel_lower_bound(df: pd.DataFrame, nodes: list) -> float:
    speeds = np.array([n["processing_speed"] for n in nodes], dtype=float)
    latencies = np.array([n["network_latency"] / 1000.0 for n in nodes], dtype=float)
    workloads = df["workload_size"].to_numpy(dtype=float)
    arrivals = df["arrival_time"].to_numpy(dtype=float)

    total_work_bound = float(workloads.sum() / max(speeds.sum(), 1e-9))
    fastest_task_duration = np.min(
        latencies.reshape(1, -1) + workloads.reshape(-1, 1) / speeds.reshape(1, -1),
        axis=1,
    )
    release_bound = float((arrivals + fastest_task_duration).max() - arrivals.min())
    longest_task_bound = float(fastest_task_duration.max())
    return max(total_work_bound, release_bound, longest_task_bound, 1e-9)


def compute_metrics(df: pd.DataFrame, tasks_per_node: list, nodes: list = None) -> dict:
    ct = df["completion_time"].dropna()
    finish_times = _finish_times(df)
    first_arrival = float(df["arrival_time"].min())
    makespan = float(finish_times.max() - first_arrival)
    throughput = len(df) / makespan if makespan > 0 else 0.0

    if nodes is not None:
        lower_bound = _parallel_lower_bound(df, nodes)
        slr = makespan / lower_bound if lower_bound > 0 else None
    else:
        lower_bound = None
        slr = None
 
    return {
        "avg_completion_time": float(ct.mean()),
        "p95_latency":         float(np.percentile(ct, 95)),
        "load_variance":       float(np.var(tasks_per_node)),
        "failure_rate":        float(df["failed"].mean()),
        "throughput":          float(throughput),
        "makespan":            makespan,
        "slr_lower_bound":      lower_bound,
        "slr":                 slr,
    }


def build_metrics_table(all_metrics: dict) -> pd.DataFrame:
    return pd.DataFrame(all_metrics).T.round(4)

