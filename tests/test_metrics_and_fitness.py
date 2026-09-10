import numpy as np
import pandas as pd

from evaluation.fitness import W_MIN, clip_weights, random_weights
from evaluation.metrics import compute_metrics
from simulation.node_environment import build_cluster


def test_slr_uses_parallel_lower_bound():
    df = pd.DataFrame(
        {
            "arrival_time": [0.0, 0.0],
            "workload_size": [10.0, 10.0],
            "completion_time": [1.0, 1.0],
            "finish_time": [1.0, 1.0],
            "failed": [False, False],
        }
    )
    nodes = [
        {"processing_speed": 10.0, "network_latency": 0.0},
        {"processing_speed": 10.0, "network_latency": 0.0},
    ]

    metrics = compute_metrics(df, tasks_per_node=[1, 1], nodes=nodes)

    assert metrics["makespan"] == 1.0
    assert metrics["slr_lower_bound"] == 1.0
    assert metrics["slr"] == 1.0


def test_policy_weights_are_nonnegative():
    clipped = clip_weights(np.array([-3.0, 1.0, 9.0]))

    assert clipped.min() >= W_MIN
    assert clipped.tolist() == [0.0, 1.0, 5.0]


def test_random_weights_respect_bounds():
    weights = random_weights(np.random.default_rng(123))

    assert weights.shape == (6,)
    assert weights.min() >= 0.0
    assert weights.max() <= 5.0


def test_default_cluster_matches_manuscript_tier_counts():
    nodes = build_cluster(15, rng=np.random.default_rng(42))
    tiers = [node["tier"] for node in nodes]

    assert tiers.count("high") == 5
    assert tiers.count("medium") == 7
    assert tiers.count("low") == 3
