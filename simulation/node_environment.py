import numpy as np


def _tier_counts(n_nodes: int) -> dict:
    if n_nodes <= 0:
        raise ValueError("n_nodes must be positive.")

    ratios = {"high": 5 / 15, "medium": 7 / 15, "low": 3 / 15}
    raw = {tier: n_nodes * ratio for tier, ratio in ratios.items()}
    counts = {tier: int(np.floor(value)) for tier, value in raw.items()}

    remaining = n_nodes - sum(counts.values())
    by_fraction = sorted(
        raw,
        key=lambda tier: raw[tier] - counts[tier],
        reverse=True,
    )
    for tier in by_fraction[:remaining]:
        counts[tier] += 1

    if n_nodes >= 3:
        for tier in ratios:
            if counts[tier] == 0:
                donor = max(counts, key=counts.get)
                counts[donor] -= 1
                counts[tier] += 1

    return counts


def build_cluster(n_nodes: int = 15, rng: np.random.Generator = None) -> list:
    if rng is None:
        rng = np.random.default_rng(42)

    counts = _tier_counts(n_nodes)
    tiers = {
        "high":   {"speed": (8, 12), "latency": (5, 20),  "fail": (0.00, 0.01), "count": counts["high"]},
        "medium": {"speed": (4, 8),  "latency": (15, 40), "fail": (0.01, 0.03), "count": counts["medium"]},
        "low":    {"speed": (2, 4),  "latency": (30, 60), "fail": (0.02, 0.05), "count": counts["low"]},
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

