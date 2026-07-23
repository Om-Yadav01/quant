import numpy as np

def build_cluster(n_nodes: int = 15, rng: np.random.Generator = None) -> list:
    if rng is None:
        rng = np.random.default_rng(42)

    tiers = {
        "high":   {"speed": (8, 12), "latency": (5, 20),  "fail": (0.00, 0.01), "count": 4},
        "medium": {"speed": (4, 8),  "latency": (15, 40), "fail": (0.01, 0.03), "count": 7},
        "low":    {"speed": (2, 4),  "latency": (30, 60), "fail": (0.02, 0.05), "count": 4},
    }

    nodes = []
    nid   = 0
    for tier, cfg in tiers.items():
        for _ in range(cfg["count"]):
            nodes.append({
                "node_id":             nid,
                "tier":                tier,
                "processing_speed":    round(rng.uniform(*cfg["speed"]),   2),
                "network_latency":     round(rng.uniform(*cfg["latency"]), 2),
                "failure_probability": round(rng.uniform(*cfg["fail"]),    4),
                "queue_workload":      0.0,
                "last_update_time":    0.0,
                "tasks_handled":       0,
            })
            nid += 1
    return nodes

def drain_queues(nodes: list, current_time: float) -> None:
    for nd in nodes:
        elapsed   = max(current_time - nd["last_update_time"], 0.0)
        work_done = elapsed * nd["processing_speed"]
        nd["queue_workload"]   = max(nd["queue_workload"] - work_done, 0.0)
        nd["last_update_time"] = current_time


def estimate_completion_time(node: dict, workload_size: float) -> float:
    return (
        node["network_latency"]  / 1000.0
        + workload_size          / node["processing_speed"]
        + node["queue_workload"] / node["processing_speed"]
    )


