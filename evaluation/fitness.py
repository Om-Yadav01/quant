import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.task_generator    import get_workload
from simulation.node_environment  import build_cluster
from simulation.simulation_runner import run_simulation
from schedulers.policy_scheduler  import PolicyScheduler
from evaluation.metrics           import compute_metrics

ALPHA = 0.35  # avg_completion_time  (primary — mean latency)
BETA  = 0.15  # load_variance        (load balance)
GAMMA = 0.20  # failure_rate         (reliability — increased from 0.15)
DELTA = 0.30  # makespan             (slightly reduced to give failure more weight)
EPS   = 1e-9 

W_MIN = -5.0
W_MAX =  5.0
N_WEIGHTS = 6

N_TASKS  = 1000
N_NODES  = 15
RNG_SEED = 42

_BASELINE = {
    "avg_completion_time": 5.0,    
    "load_variance"      : 1000.0, 
    "failure_rate"       : 0.006,  
    "makespan"           : 10.0,   
}

def set_baselines(avg_ct: float, load_variance: float,
                  failure_rate: float, makespan: float) -> None:
    _BASELINE["avg_completion_time"] = max(avg_ct,       1e-9)
    _BASELINE["makespan"]            = max(makespan,     1e-9)
    _BASELINE["failure_rate"]        = max(failure_rate, 1e-9)

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
 
        lat_norm  = metrics["avg_completion_time"] / max(_BASELINE["avg_completion_time"], EPS)
        var_norm  = metrics["load_variance"]        / max(_BASELINE["load_variance"],       EPS)
        fail_norm = metrics["failure_rate"]         / max(_BASELINE["failure_rate"],        EPS)
        ms_norm   = metrics["makespan"]             / max(_BASELINE["makespan"],            EPS)
 
        fitness = (
            ALPHA * lat_norm
            + BETA  * var_norm
            + GAMMA * fail_norm
            + DELTA * ms_norm
        )
        
        if fail_norm > 1.0:
            fitness += 0.10 * (fail_norm - 1.0)
 
        return float(fitness)
 
    except Exception as e:
        return 1e6
    
def clip_weights(weights) -> np.ndarray:
    return np.clip(weights, W_MIN, W_MAX)
 
 
def random_weights(rng: np.random.Generator = None) -> np.ndarray:
    if rng is None:
        rng = np.random.default_rng()
    return rng.uniform(W_MIN, W_MAX, size=N_WEIGHTS)
