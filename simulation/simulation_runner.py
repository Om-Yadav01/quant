import copy
import numpy as np
import pandas as pd

from simulation.node_environment import drain_queues, estimate_completion_time

MAX_RETRIES = 2


def run_simulation(
    workload_df:  pd.DataFrame,
    scheduler,
    base_cluster: list,
    rng:          np.random.Generator = None,
) -> tuple:
    if rng is None:
        rng = np.random.default_rng(42)

    scheduler.reset()
    nodes   = copy.deepcopy(base_cluster)
    results = []

    for _, task in workload_df.iterrows():
        t_arr   = task["arrival_time"]
        w_size  = task["workload_size"]
        task_id = int(task["task_id"])

        drain_queues(nodes, t_arr)

        assigned    = False
        attempts    = 0
        chosen_node = None
        comp_time   = np.nan
        failed_flag = False

        while attempts <= MAX_RETRIES:
            node_idx  = scheduler.select(nodes, w_size)
            node      = nodes[node_idx]
            comp_time = estimate_completion_time(node, w_size)

            if rng.random() < node["failure_probability"]:
                attempts   += 1
                failed_flag = True
                drain_queues(nodes, t_arr + attempts * 0.1)
                continue

            node["queue_workload"] += w_size
            node["tasks_handled"]  += 1
            chosen_node = node_idx
            assigned    = True
            break

        if not assigned:
            node_idx  = int(np.argmin([nd["queue_workload"] for nd in nodes]))
            node      = nodes[node_idx]
            comp_time = estimate_completion_time(node, w_size)
            node["queue_workload"] += w_size
            node["tasks_handled"]  += 1
            chosen_node = node_idx

        results.append({
            "task_id":         task_id,
            "arrival_time":    t_arr,
            "workload_size":   w_size,
            "node_id":         chosen_node,
            "completion_time": comp_time,
            "failed":          failed_flag,
            "retries":         attempts,
        })

    tasks_per_node = [nd["tasks_handled"] for nd in nodes]
    return pd.DataFrame(results), tasks_per_node

