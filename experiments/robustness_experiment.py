import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evaluation.fitness import set_baselines_from_metrics, set_workload_cache
from evaluation.metrics import compute_metrics
from optimizers.de_optimizer import DifferentialEvolution
from schedulers.least_loaded import LeastLoadedScheduler
from schedulers.mect import MECTScheduler
from schedulers.policy_scheduler import PolicyScheduler
from schedulers.round_robin import RoundRobinScheduler
from simulation.node_environment import build_cluster
from simulation.simulation_runner import run_simulation
from simulation.task_generator import get_workload


RNG_SEED = 42
CSV_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "csv"
)


SCENARIOS = [
    {"scenario": "baseline", "seed": 42, "arrival_window": 600.0, "workload_scale": 1.0, "nodes": 15},
    {"scenario": "sample_seed_101", "seed": 101, "arrival_window": 600.0, "workload_scale": 1.0, "nodes": 15},
    {"scenario": "sample_seed_202", "seed": 202, "arrival_window": 600.0, "workload_scale": 1.0, "nodes": 15},
    {"scenario": "compressed_300s", "seed": 42, "arrival_window": 300.0, "workload_scale": 1.0, "nodes": 15},
    {"scenario": "relaxed_1200s", "seed": 42, "arrival_window": 1200.0, "workload_scale": 1.0, "nodes": 15},
    {"scenario": "light_workload", "seed": 42, "arrival_window": 600.0, "workload_scale": 0.75, "nodes": 15},
    {"scenario": "heavy_workload", "seed": 42, "arrival_window": 600.0, "workload_scale": 1.25, "nodes": 15},
    {"scenario": "small_cluster", "seed": 42, "arrival_window": 600.0, "workload_scale": 1.0, "nodes": 10},
    {"scenario": "large_cluster", "seed": 42, "arrival_window": 600.0, "workload_scale": 1.0, "nodes": 25},
]

REFERENCE_POLICY_WEIGHTS = [2.0, 4.5, 2.0, 2.0, 4.5, 1.5]


def _run_scheduler(name, scheduler, workload, base_nodes, seed):
    start = time.perf_counter()
    df, tasks_per_node = run_simulation(
        workload, scheduler, base_nodes, rng=np.random.default_rng(seed)
    )
    elapsed = time.perf_counter() - start
    metrics = compute_metrics(df, tasks_per_node, base_nodes)
    return {"scheduler": name, "runtime_sec": elapsed, **metrics}


def _scenario_inputs(config, num_tasks):
    rng = np.random.default_rng(config["seed"])
    workload = get_workload(
        num_tasks=num_tasks,
        rng=rng,
        arrival_window=config["arrival_window"],
        workload_scale=config["workload_scale"],
    )
    base_nodes = build_cluster(config["nodes"], rng=rng)
    return workload, base_nodes


def run_robustness_experiment(num_tasks, reoptimize_de, pop_size, iterations):
    rows = []
    for scenario_index, config in enumerate(SCENARIOS):
        print(f"\n[robustness] Scenario: {config['scenario']}")
        workload, base_nodes = _scenario_inputs(config, num_tasks)

        mect_result = _run_scheduler(
            "MECT", MECTScheduler(), workload, base_nodes, config["seed"]
        )
        set_workload_cache(workload, base_nodes)
        set_baselines_from_metrics(mect_result)

        schedulers = {
            "Round Robin": RoundRobinScheduler(),
            "Least Loaded": LeastLoadedScheduler(),
            "MECT": MECTScheduler(),
            "Reference Policy": PolicyScheduler(REFERENCE_POLICY_WEIGHTS),
        }

        if reoptimize_de:
            optimizer = DifferentialEvolution(
                pop_size=pop_size,
                iterations=iterations,
                seed=RNG_SEED + scenario_index,
            )
            result = optimizer.run(verbose=False)
            schedulers["Reoptimized DE Policy"] = PolicyScheduler(result["best_weights"])

        for name, scheduler in schedulers.items():
            result = _run_scheduler(
                name,
                scheduler,
                workload,
                base_nodes,
                config["seed"] + scenario_index + 1000,
            )
            result.update(config)
            rows.append(result)

    os.makedirs(CSV_DIR, exist_ok=True)
    out_path = os.path.join(CSV_DIR, "robustness_scenarios.csv")
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"\n[robustness] Saved: {out_path}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Run robustness checks across samples, windows, intensities, and cluster sizes."
    )
    parser.add_argument("--tasks", type=int, default=500)
    parser.add_argument("--reoptimize-de", action="store_true")
    parser.add_argument("--pop-size", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=10)
    args = parser.parse_args()

    run_robustness_experiment(
        num_tasks=args.tasks,
        reoptimize_de=args.reoptimize_de,
        pop_size=args.pop_size,
        iterations=args.iterations,
    )


if __name__ == "__main__":
    main()
