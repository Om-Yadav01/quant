"""
experiments/test_policy_scheduler.py
─────────────────────────────────────────────────────────────────────────────
Test and demonstration script for PolicyScheduler.

Shows:
  1. How PolicyScheduler integrates with simulation_runner (drop-in, no
     changes to runner needed).
  2. How different weight vectors produce different scheduling decisions and
     measurably different performance metrics.
  3. Score breakdown — what each weight contributes per node.
  4. Comparison table: baselines vs policy variants.

Run from project root:
    python experiments/test_policy_scheduler.py
─────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simulation.task_generator    import get_workload
from simulation.node_environment  import build_cluster
from simulation.simulation_runner import run_simulation
from schedulers.round_robin       import RoundRobinScheduler
from schedulers.least_loaded      import LeastLoadedScheduler
from schedulers.mect              import MECTScheduler
from schedulers.policy_scheduler  import PolicyScheduler, WEIGHT_LABELS, N_WEIGHTS
from evaluation.metrics           import compute_metrics, build_metrics_table

RNG_SEED = 42
N_TASKS  = 1000
N_NODES  = 15


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHT VECTOR PRESETS
# Each preset emphasises a different scheduling concern.
# These represent the range of behaviours the optimizer will search through.
# ─────────────────────────────────────────────────────────────────────────────

WEIGHT_PRESETS = {
    # Neutral — equal weight to all features
    "Policy [Equal]": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],

    # Speed-first — strongly prefers fastest nodes, ignores everything else
    "Policy [Speed-First]": [2.0, 0.2, 0.2, 0.2, 0.5, 0.2],

    # Load-aware — heavily penalises queue depth (similar to Least Loaded
    # but with additional features)
    "Policy [Load-Aware]": [0.5, 2.0, 0.5, 0.5, 1.5, 0.5],

    # Reliability-first — heavily penalises failure probability
    "Policy [Reliability]": [0.5, 0.5, 0.5, 3.0, 0.5, 0.5],

    # Latency-sensitive — penalises network latency and execution cost
    "Policy [Low-Latency]": [1.0, 1.0, 2.5, 0.5, 1.0, 2.0],

    # Balanced — tuned heuristically to balance all six concerns
    "Policy [Balanced]": [1.5, 1.2, 0.8, 1.0, 1.3, 1.1],
}


def run_all(workload, base_nodes, rng):
    """Run all schedulers (baselines + policy presets) and collect metrics."""

    schedulers = {
        # ── Baselines ──────────────────────────────────────────────────────
        "Round Robin"  : RoundRobinScheduler(),
        "Least Loaded" : LeastLoadedScheduler(),
        "MECT"         : MECTScheduler(),
        # ── Policy presets ─────────────────────────────────────────────────
        **{name: PolicyScheduler(w) for name, w in WEIGHT_PRESETS.items()}
    }

    all_results  = {}
    all_metrics  = {}
    all_per_node = {}

    print(f"\n{'─'*70}")
    print(f"  {'Scheduler':<30} {'AvgCT':>8} {'P95':>8} {'Var':>10} "
          f"{'FailR':>7} {'Tput':>8}")
    print(f"{'─'*70}")

    for name, sched in schedulers.items():
        t0             = time.perf_counter()
        df, tpn        = run_simulation(workload, sched, base_nodes, rng=rng)
        elapsed        = time.perf_counter() - t0
        metrics        = compute_metrics(df, tpn,base_nodes)

        all_results[name]  = df
        all_metrics[name]  = metrics
        all_per_node[name] = tpn

        print(f"  {name:<30} "
              f"{metrics['avg_completion_time']:>8.4f} "
              f"{metrics['p95_latency']:>8.4f} "
              f"{metrics['load_variance']:>10.2f} "
              f"{metrics['failure_rate']:>7.4f} "
              f"{metrics['throughput']:>8.4f}"
              f"  ({elapsed*1000:.1f}ms)")

    print(f"{'─'*70}")
    return all_results, all_metrics, all_per_node


def demo_score_breakdown(nodes, workload_size=50.0):
    """
    Show how a single scheduling decision changes with different weight vectors.

    Prints per-node scores for one representative task under three weight
    presets, demonstrating that different weights select different nodes.
    """
    print("\n" + "="*70)
    print("  SCORE BREAKDOWN DEMO")
    print(f"  Task workload_size = {workload_size} units")
    print("="*70)

    demo_presets = {
        "Speed-First" : WEIGHT_PRESETS["Policy [Speed-First]"],
        "Load-Aware"  : WEIGHT_PRESETS["Policy [Load-Aware]"],
        "Reliability" : WEIGHT_PRESETS["Policy [Reliability]"],
    }

    for preset_name, weights in demo_presets.items():
        sched     = PolicyScheduler(weights)
        breakdown = sched.score_breakdown(nodes, workload_size)

        # Sort by final score to show ranking
        breakdown.sort(key=lambda x: x["final_score"], reverse=True)

        print(f"\n  Weights [{preset_name}]: "
              + " | ".join(f"w{i+1}={w:.1f}" for i, w in enumerate(weights)))
        print(f"  {'Rank':<5} {'Node':>5} {'Tier':>8} "
              f"{'Speed':>7} {'Queue':>7} {'Latency':>9} "
              f"{'FailP':>7} {'Score':>8}  {'→ Selected' if True else ''}")
        print(f"  {'─'*75}")

        for rank, row in enumerate(breakdown[:5]):   # show top 5
            node_info = next(n for n in nodes if n["node_id"] == row["node_id"])
            marker    = "  ← SELECTED" if rank == 0 else ""
            print(f"  {rank+1:<5} "
                  f"N{row['node_id']:>3}  "
                  f"{node_info['tier']:>8}  "
                  f"{row['raw_speed']:>6.2f}  "
                  f"{row['raw_queue']:>6.2f}  "
                  f"{row['raw_latency']:>8.2f}  "
                  f"{row['raw_fail_p']:>6.4f}  "
                  f"{row['final_score']:>8.4f}"
                  f"{marker}")


def demo_weight_sensitivity(workload, base_nodes, rng):
    """
    Show how individual weight changes affect average completion time.

    Sweeps each weight from 0 → 3 while holding others at 1.0.
    This is the kind of sensitivity analysis that validates the scoring model
    before running the full Phase-2 optimizer.
    """
    print("\n" + "="*70)
    print("  WEIGHT SENSITIVITY ANALYSIS")
    print("  (sweep each weight 0→3, all others fixed at 1.0)")
    print("="*70)

    sweep_values = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]

    for wi in range(N_WEIGHTS):
        label = WEIGHT_LABELS[wi]
        print(f"\n  {label}")
        print(f"  {'Weight':>8} {'AvgCT':>10} {'P95':>10} {'LoadVar':>12}")
        print(f"  {'─'*45}")

        for val in sweep_values:
            w = [1.0] * N_WEIGHTS
            w[wi] = val
            sched = PolicyScheduler(w)
            df, tpn = run_simulation(workload, sched, base_nodes,
                                     rng=np.random.default_rng(RNG_SEED))
            m = compute_metrics(df, tpn,base_nodes)
            print(f"  {val:>8.1f} "
                  f"{m['avg_completion_time']:>10.4f} "
                  f"{m['p95_latency']:>10.4f} "
                  f"{m['load_variance']:>12.2f}")


def main():
    rng        = np.random.default_rng(RNG_SEED)
    workload   = get_workload(N_TASKS, rng=rng)
    base_nodes = build_cluster(N_NODES, rng=rng)

    print("="*70)
    print("  PolicyScheduler — Integration Test & Weight Sensitivity Demo")
    print("="*70)
    print(f"\n  Workload : {N_TASKS} tasks")
    print(f"  Cluster  : {N_NODES} nodes (heterogeneous, 3-tier)")
    print(f"\n  Weight vector structure:")
    for i, label in enumerate(WEIGHT_LABELS):
        print(f"    W[{i}] = {label}")

    # ── 1. Full comparison table ──────────────────────────────────────────────
    print(f"\n\n  [1/3] FULL SCHEDULER COMPARISON")
    all_results, all_metrics, all_per_node = run_all(workload, base_nodes, rng)

    # Find best policy variant
    policy_names  = list(WEIGHT_PRESETS.keys())
    best_policy   = min(policy_names, key=lambda n: all_metrics[n]["avg_completion_time"])
    mect_avg      = all_metrics["MECT"]["avg_completion_time"]
    best_avg      = all_metrics[best_policy]["avg_completion_time"]
    improvement   = (mect_avg - best_avg) / mect_avg * 100

    print(f"\n  Best policy preset : {best_policy}")
    print(f"  MECT avg CT        : {mect_avg:.4f}s")
    print(f"  Best policy avg CT : {best_avg:.4f}s")
    print(f"  Improvement vs MECT: {improvement:+.2f}%")

    # ── 2. Score breakdown demo ───────────────────────────────────────────────
    print(f"\n\n  [2/3] SCORE BREAKDOWN FOR A SINGLE TASK DECISION")
    demo_score_breakdown(base_nodes, workload_size=50.0)

    # ── 3. Weight sensitivity ─────────────────────────────────────────────────
    print(f"\n\n  [3/3] WEIGHT SENSITIVITY ANALYSIS")
    demo_weight_sensitivity(workload, base_nodes, rng)

    # ── 4. Save results ───────────────────────────────────────────────────────
    metrics_df = build_metrics_table(all_metrics)
    out_path   = "../results/csv/policy_scheduler_test.csv"
    metrics_df.to_csv(out_path)
    print(f"\n\n[✓] Results saved → {out_path}")

    print("\n" + "="*70)
    print("  INTEGRATION EXAMPLE  (drop into run_baselines.py)")
    print("="*70)
    print("""
    from schedulers.policy_scheduler import PolicyScheduler

    # Phase-2: optimizer provides this weight vector as a candidate solution
    weights   = [1.5, 1.2, 0.8, 1.0, 1.3, 1.1]
    scheduler = PolicyScheduler(weights)

    # Exact same call as baseline schedulers — no changes to runner needed
    df, tasks_per_node = run_simulation(workload, scheduler, base_nodes, rng=rng)
    metrics            = compute_metrics(df, tasks_per_node)

    # Fitness value for the optimizer to minimise
    fitness = metrics["avg_completion_time"]
    """)

    return all_results, all_metrics


if __name__ == "__main__":
    main()
