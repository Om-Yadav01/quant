import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.task_generator    import get_workload
from simulation.node_environment  import build_cluster
from simulation.simulation_runner import run_simulation
from schedulers.policy_scheduler  import PolicyScheduler
from evaluation.metrics           import compute_metrics

DEFAULT_FITNESS_WEIGHTS = {
    "avg_completion_time": 0.25,
    "p95_latency":         0.20,
    "makespan":            0.20,
    "load_variance":       0.10,
    "failure_rate":        0.15,
    "slr":                 0.10,
}
FITNESS_WEIGHTS = DEFAULT_FITNESS_WEIGHTS.copy()
EPS = 1e-9

W_MIN =  0.0
W_MAX =  5.0
N_WEIGHTS = 6

N_TASKS  = 1000
N_NODES  = 15
RNG_SEED = 42

_BASELINE = {
    "avg_completion_time": 1.0,
    "p95_latency"        : 1.0,
    "makespan"           : 1.0,
    "load_variance"      : 1.0,
    "failure_rate"       : 1.0,
    "slr"                : 1.0,
}

def set_baselines(avg_ct: float, load_variance: float,
                  failure_rate: float, makespan: float,
                  p95_latency: float = None, slr: float = None) -> None:
    _BASELINE["avg_completion_time"] = max(avg_ct,       1e-9)
    if p95_latency is not None:
        _BASELINE["p95_latency"] = max(p95_latency, 1e-9)
    _BASELINE["makespan"]            = max(makespan,     1e-9)
    _BASELINE["load_variance"]       = max(load_variance, 1e-9)
    _BASELINE["failure_rate"]        = max(failure_rate, 1e-9)
    if slr is not None:
        _BASELINE["slr"] = max(slr, 1e-9)


def set_baselines_from_metrics(metrics: dict) -> None:
    set_baselines(
        avg_ct=metrics["avg_completion_time"],
        p95_latency=metrics["p95_latency"],
        makespan=metrics["makespan"],
        load_variance=metrics["load_variance"],
        failure_rate=max(metrics["failure_rate"], EPS),
        slr=metrics["slr"],
    )


def set_fitness_weights(weights: dict) -> None:
    missing = set(FITNESS_WEIGHTS) - set(weights)
    extra = set(weights) - set(FITNESS_WEIGHTS)
    if missing or extra:
        raise ValueError(f"Fitness weight keys mismatch. Missing={missing}, extra={extra}")

    total = sum(float(v) for v in weights.values())
    if total <= 0:
        raise ValueError("Fitness weights must sum to a positive value.")

    for key, value in weights.items():
        if value < 0:
            raise ValueError(f"Fitness weight for {key} must be nonnegative.")
        FITNESS_WEIGHTS[key] = float(value) / total

class WorkloadCache:
    def __init__(self):
        self._workload = None
        self._nodes    = None
        
    def set(self, workload, nodes) -> None:
        self._workload = workload
        self._nodes    = nodes
        print(f"[fitness] Workload injected: {len(self._workload)} tasks, "
              f"{len(self._nodes)} nodes")
 
    def get(self):
        if self._workload is None or self._nodes is None:
            rng            = np.random.default_rng(RNG_SEED)
            self._workload = get_workload(N_TASKS, rng=rng)
            self._nodes    = build_cluster(N_NODES, rng=rng)
            print(f"[fitness] Workload cached: {len(self._workload)} tasks, "
                  f"{len(self._nodes)} nodes")
        return self._workload, self._nodes
    
_cache = WorkloadCache()

def set_workload_cache(workload, nodes) -> None:
    _cache.set(workload, nodes)

def evaluate_weights(weights) -> float:
    try:
        workload, base_nodes = _cache.get()
 
        rng       = np.random.default_rng(RNG_SEED)
        scheduler = PolicyScheduler(weights)
 
        df, tasks_per_node = run_simulation(
            workload, scheduler, base_nodes, rng=rng
        )
 
        metrics = compute_metrics(df, tasks_per_node, base_nodes)
 
        norm = {
            key: metrics[key] / max(_BASELINE[key], EPS)
            for key in FITNESS_WEIGHTS
        }
 
        fitness = sum(FITNESS_WEIGHTS[key] * norm[key] for key in FITNESS_WEIGHTS)
        
        if norm["failure_rate"] > 1.0:
            fitness += 0.05 * (norm["failure_rate"] - 1.0)
 
        return float(fitness)
 
    except Exception as e:
        return 1e6
    
def clip_weights(weights) -> np.ndarray:
    return np.clip(weights, W_MIN, W_MAX)
 
 
def random_weights(rng: np.random.Generator = None) -> np.ndarray:
    if rng is None:
        rng = np.random.default_rng()
    return rng.uniform(W_MIN, W_MAX, size=N_WEIGHTS)
