import numpy as np
 
WEIGHT_LABELS = [
    "w1_processing_speed",
    "w2_queue_workload",
    "w3_network_latency",
    "w4_failure_probability",
    "w5_available_capacity",
    "w6_execution_cost",
]

N_WEIGHTS = len(WEIGHT_LABELS)
DEFAULT_WEIGHTS = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

def _minmax_normalize(values: np.ndarray) -> np.ndarray:
    v_min = values.min()
    v_max = values.max()
    span  = v_max - v_min
    if span < 1e-12:
        return np.zeros_like(values, dtype=float)
    return (values - v_min) / span

class PolicyScheduler:
    def __init__(self, weights=None):
        if weights is None:
            weights = DEFAULT_WEIGHTS
        self.weights = np.array(weights, dtype=float)
 
        if len(self.weights) != N_WEIGHTS:
            raise ValueError(
                f"PolicyScheduler expects {N_WEIGHTS} weights, "
                f"got {len(self.weights)}."
            )
 
        self.name = (
            f"Policy["
            + ", ".join(f"{w:.2f}" for w in self.weights)
            + "]"
        )
        
    def _compute_scores(self, nodes: list, workload_size: float) -> np.ndarray:
        n = len(nodes)
        w = self.weights
 
        speed    = np.array([nd["processing_speed"]    for nd in nodes], dtype=float)
        queue    = np.array([nd["queue_workload"]       for nd in nodes], dtype=float)
        latency  = np.array([nd["network_latency"]      for nd in nodes], dtype=float)
        fail_p   = np.array([nd["failure_probability"]  for nd in nodes], dtype=float)
 
        avail_cap = np.clip(speed - queue / np.maximum(speed, 1e-9), 0.0, None)
 
        exec_cost = workload_size / np.maximum(speed, 1e-9)
 
        f1 = _minmax_normalize(speed)
        f2 = _minmax_normalize(queue)
        f3 = _minmax_normalize(latency)
        f4 = _minmax_normalize(fail_p)
        f5 = _minmax_normalize(avail_cap)
        f6 = _minmax_normalize(exec_cost)
 
        scores = (
            + w[0] * f1   # higher speed     → boost score
            - w[1] * f2   # higher queue      → penalise
            - w[2] * f3   # higher latency    → penalise
            - w[3] * f4   # higher fail prob  → penalise
            + w[4] * f5   # higher capacity   → boost score
            - w[5] * f6   # higher exec cost  → penalise
        )
 
        return scores
    
    def select(self, nodes: list, workload_size: float) -> int:
        scores = self._compute_scores(nodes, workload_size)
        return int(np.argmax(scores))
    
    def reset(self) -> None:
        pass
    
    def update_weights(self, new_weights) -> None:
        new_weights = np.array(new_weights, dtype=float)
        if len(new_weights) != N_WEIGHTS:
            raise ValueError(
                f"Expected {N_WEIGHTS} weights, got {len(new_weights)}."
            )
        self.weights = new_weights
        self.name = (
            f"Policy["
            + ", ".join(f"{w:.2f}" for w in self.weights)
            + "]"
        )
        
    def get_weights(self) -> np.ndarray:
        return self.weights.copy()
    
    def score_breakdown(self, nodes: list, workload_size: float) -> list:
        n = len(nodes)
        w = self.weights
 
        speed    = np.array([nd["processing_speed"]   for nd in nodes], dtype=float)
        queue    = np.array([nd["queue_workload"]      for nd in nodes], dtype=float)
        latency  = np.array([nd["network_latency"]     for nd in nodes], dtype=float)
        fail_p   = np.array([nd["failure_probability"] for nd in nodes], dtype=float)
        avail_cap = np.clip(speed - queue / np.maximum(speed, 1e-9), 0.0, None)
        exec_cost = workload_size / np.maximum(speed, 1e-9)
 
        f1 = _minmax_normalize(speed)
        f2 = _minmax_normalize(queue)
        f3 = _minmax_normalize(latency)
        f4 = _minmax_normalize(fail_p)
        f5 = _minmax_normalize(avail_cap)
        f6 = _minmax_normalize(exec_cost)
 
        breakdown = []
        for i, nd in enumerate(nodes):
            breakdown.append({
                "node_id"          : nd["node_id"],
                # raw features
                "raw_speed"        : speed[i],
                "raw_queue"        : queue[i],
                "raw_latency"      : latency[i],
                "raw_fail_p"       : fail_p[i],
                "raw_avail_cap"    : avail_cap[i],
                "raw_exec_cost"    : exec_cost[i],

                "norm_speed"       : f1[i],
                "norm_queue"       : f2[i],
                "norm_latency"     : f3[i],
                "norm_fail_p"      : f4[i],
                "norm_avail_cap"   : f5[i],
                "norm_exec_cost"   : f6[i],

                "contrib_speed"    : +w[0] * f1[i],
                "contrib_queue"    : -w[1] * f2[i],
                "contrib_latency"  : -w[2] * f3[i],
                "contrib_fail_p"   : -w[3] * f4[i],
                "contrib_avail_cap": +w[4] * f5[i],
                "contrib_exec_cost": -w[5] * f6[i],
            
                "final_score"      : (
                    + w[0]*f1[i] - w[1]*f2[i] - w[2]*f3[i]
                    - w[3]*f4[i] + w[4]*f5[i] - w[5]*f6[i]
                ),
            })
        return breakdown
    
    def __repr__(self) -> str:
        lines = ["PolicyScheduler weights:"]
        for label, w in zip(WEIGHT_LABELS, self.weights):
            lines.append(f"  {label:<28s}: {w:.4f}")
        return "\n".join(lines)
