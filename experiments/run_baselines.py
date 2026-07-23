import os
import sys
import time
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.task_generator import get_workload,load_tasks_from_dataset
from simulation.node_environment import build_cluster
from simulation.simulation_runner import run_simulation
from schedulers.round_robin import RoundRobinScheduler
from schedulers.least_loaded import LeastLoadedScheduler
from schedulers.mect import MECTScheduler
from evaluation.metrics import compute_metrics, build_metrics_table
from visualization.plot_results import plot_results

RNG_SEED  = 42
N_TASKS   = 1000
N_NODES   = 15
CSV_DIR   = "../results/csv"
PLOTS_DIR = "../results/plots"


def run_baselines() -> tuple:
    rng = np.random.default_rng(RNG_SEED)

    workload   = get_workload(N_TASKS, rng=rng)
    base_nodes = build_cluster(N_NODES,    rng=rng)

    print(f"\n[Workload]  {len(workload)} tasks | "
          f"arrival window: {workload.arrival_time.max():.1f}s | "
          f"workload range: {workload.workload_size.min()}–"
          f"{workload.workload_size.max()} units")
    print(f"[Cluster]   {len(base_nodes)} nodes | "
          f"speed range: {min(n['processing_speed'] for n in base_nodes)}–"
          f"{max(n['processing_speed'] for n in base_nodes)} u/s | "
          f"latency range: {min(n['network_latency'] for n in base_nodes)}–"
          f"{max(n['network_latency'] for n in base_nodes)} ms")

    schedulers = {
        "Round Robin":  RoundRobinScheduler(),
        "Least Loaded": LeastLoadedScheduler(),
        "MECT":         MECTScheduler(),
    }

    all_results  = {}
    all_metrics  = {}
    all_per_node = {}

    for name, sched in schedulers.items():
        t0               = time.perf_counter()
        df, tasks_per_nd = run_simulation(workload, sched, base_nodes, rng=rng)
        elapsed          = time.perf_counter() - t0
        metrics          = compute_metrics(df, tasks_per_nd, base_nodes)
 
        all_results[name]  = df
        all_metrics[name]  = metrics
        all_per_node[name] = tasks_per_nd
 
        print(f"\n[{name}]  (sim runtime: {elapsed * 1000:.1f} ms)")
        for k, v in metrics.items():
            print(f"   {k:<28s}: {v:.4f}")

    print("\n" + "─" * 68)
    print("  SUMMARY TABLE")
    print("─" * 68)
    metrics_df = build_metrics_table(all_metrics)
    print(metrics_df.to_string())
    
    ALIBABA_FAILED     = 83276
    ALIBABA_TERMINATED = 14059143
    real_fail_rate     = ALIBABA_FAILED / (ALIBABA_FAILED + ALIBABA_TERMINATED)
    sim_fail_rate      = all_metrics["MECT"]["failure_rate"]
    print(f"\n[Alibaba Trace] Real failure rate      : {real_fail_rate:.4f} ({real_fail_rate*100:.2f}%)")
    print(f"[Simulator]     Modelled failure rate  : {sim_fail_rate:.4f} ({sim_fail_rate*100:.2f}%)")

    os.makedirs(CSV_DIR, exist_ok=True)
    csv_path = os.path.join(CSV_DIR, "baseline_metrics.csv")
    metrics_df.to_csv(csv_path)

    for name, df in all_results.items():
        slug     = name.lower().replace(" ", "_")
        raw_path = os.path.join(CSV_DIR, f"results_{slug}.csv")
        df.to_csv(raw_path, index=False)

    plot_results(all_results, all_metrics, all_per_node, save_dir=PLOTS_DIR)

    best_avg = min(all_metrics, key=lambda n: all_metrics[n]["avg_completion_time"])
    best_p95 = min(all_metrics, key=lambda n: all_metrics[n]["p95_latency"])
    best_var = min(all_metrics, key=lambda n: all_metrics[n]["load_variance"])

    return all_results, all_metrics, all_per_node


if __name__ == "__main__":
    run_baselines()

