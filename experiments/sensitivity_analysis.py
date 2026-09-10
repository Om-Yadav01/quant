import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.fitness import (
    DEFAULT_FITNESS_WEIGHTS,
    set_baselines_from_metrics,
    set_fitness_weights,
    set_workload_cache,
)
from evaluation.metrics import compute_metrics
from optimizers.de_optimizer import DifferentialEvolution
from schedulers.mect import MECTScheduler
from schedulers.policy_scheduler import PolicyScheduler
from simulation.node_environment import build_cluster
from simulation.simulation_runner import run_simulation
from simulation.task_generator import get_workload


RNG_SEED = 42
N_NODES = 15
CSV_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "csv"
)


COEFFICIENT_PROFILES = {
    "balanced_six_objective": {
        "avg_completion_time": 0.25,
        "p95_latency": 0.20,
        "makespan": 0.20,
        "load_variance": 0.10,
        "failure_rate": 0.15,
        "slr": 0.10,
    },
    "mean_latency_heavy": {
        "avg_completion_time": 0.40,
        "p95_latency": 0.15,
        "makespan": 0.15,
        "load_variance": 0.10,
        "failure_rate": 0.10,
        "slr": 0.10,
    },
    "tail_latency_heavy": {
        "avg_completion_time": 0.20,
        "p95_latency": 0.35,
        "makespan": 0.15,
        "load_variance": 0.10,
        "failure_rate": 0.10,
        "slr": 0.10,
    },
    "makespan_slr_heavy": {
        "avg_completion_time": 0.20,
        "p95_latency": 0.15,
        "makespan": 0.30,
        "load_variance": 0.05,
        "failure_rate": 0.10,
        "slr": 0.20,
    },
    "reliability_heavy": {
        "avg_completion_time": 0.20,
        "p95_latency": 0.15,
        "makespan": 0.15,
        "load_variance": 0.10,
        "failure_rate": 0.30,
        "slr": 0.10,
    },
    "fairness_heavy": {
        "avg_completion_time": 0.20,
        "p95_latency": 0.15,
        "makespan": 0.15,
        "load_variance": 0.30,
        "failure_rate": 0.10,
        "slr": 0.10,
    },
}


def _evaluate_policy(weights, workload, base_nodes, seed):
    scheduler = PolicyScheduler(weights)
    df, tasks_per_node = run_simulation(
        workload, scheduler, base_nodes, rng=np.random.default_rng(seed)
    )
    return compute_metrics(df, tasks_per_node, base_nodes)


def run_sensitivity_analysis(num_tasks, pop_size, iterations):
    rng = np.random.default_rng(RNG_SEED)
    workload = get_workload(num_tasks, rng=rng)
    base_nodes = build_cluster(N_NODES, rng=rng)
    set_workload_cache(workload, base_nodes)

    mect_df, mect_tpn = run_simulation(
        workload, MECTScheduler(), base_nodes, rng=np.random.default_rng(RNG_SEED)
    )
    mect_metrics = compute_metrics(mect_df, mect_tpn, base_nodes)
    set_baselines_from_metrics(mect_metrics)

    rows = []
    for idx, (profile_name, coeffs) in enumerate(COEFFICIENT_PROFILES.items()):
        print(f"\n[sensitivity] Running profile: {profile_name}")
        set_fitness_weights(coeffs)

        optimizer = DifferentialEvolution(
            pop_size=pop_size,
            iterations=iterations,
            seed=RNG_SEED + idx,
        )
        start = time.perf_counter()
        result = optimizer.run(verbose=False)
        elapsed = time.perf_counter() - start
        metrics = _evaluate_policy(
            result["best_weights"], workload, base_nodes, seed=RNG_SEED + 100 + idx
        )

        row = {
            "profile": profile_name,
            "optimizer": "DE",
            "best_fitness": result["best_fitness"],
            "time_sec": elapsed,
        }
        row.update({f"coef_{key}": value for key, value in coeffs.items()})
        row.update({f"w{i + 1}": float(value) for i, value in enumerate(result["best_weights"])})
        row.update(metrics)
        rows.append(row)

    set_fitness_weights(DEFAULT_FITNESS_WEIGHTS)

    os.makedirs(CSV_DIR, exist_ok=True)
    out_path = os.path.join(CSV_DIR, "fitness_weight_sensitivity.csv")
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"\n[sensitivity] Saved: {out_path}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Run coefficient sensitivity analysis for the six-objective fitness function."
    )
    parser.add_argument("--tasks", type=int, default=500)
    parser.add_argument("--pop-size", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=10)
    args = parser.parse_args()

    run_sensitivity_analysis(
        num_tasks=args.tasks,
        pop_size=args.pop_size,
        iterations=args.iterations,
    )


if __name__ == "__main__":
    main()
