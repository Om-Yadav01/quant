import os
import sys
import time
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.task_generator    import get_workload
from simulation.node_environment  import build_cluster
from simulation.simulation_runner import run_simulation
from schedulers.round_robin       import RoundRobinScheduler
from schedulers.least_loaded      import LeastLoadedScheduler
from schedulers.mect              import MECTScheduler
from schedulers.policy_scheduler  import PolicyScheduler
from evaluation.metrics           import compute_metrics, build_metrics_table
from optimizers.ga_optimizer    import GeneticAlgorithm
from optimizers.pso_optimizer   import PSO
from optimizers.de_optimizer    import DifferentialEvolution
from evaluation.fitness         import evaluate_weights, N_WEIGHTS,set_baselines,set_workload_cache

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
 
RNG_SEED  = 42
N_TASKS   = 1000
N_NODES   = 15

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR   = os.path.join(_PROJECT_ROOT, "results", "csv")
PLOTS_DIR = os.path.join(_PROJECT_ROOT, "results", "plots")
 
def evaluate_policy(weights, workload, base_nodes, rng):
    scheduler          = PolicyScheduler(weights)
    df, tasks_per_node = run_simulation(workload, scheduler, base_nodes, rng=rng)
    return compute_metrics(df, tasks_per_node, base_nodes)

def run_optimizer_experiment():
    rng        = np.random.default_rng(RNG_SEED)
    workload   = get_workload(N_TASKS, rng=rng)
    base_nodes = build_cluster(N_NODES, rng=rng)
    
    set_workload_cache(workload, base_nodes)
    
    print("=" * 68)
    print("  Phase-2: Metaheuristic Optimization of PolicyScheduler")
    print("  Optimizers: GA | PSO | DE")
    print("=" * 68)
    print(f"\n[Workload] {len(workload)} tasks | "
          f"arrival window: {workload.arrival_time.max():.1f}s")
    print(f"[Cluster]  {len(base_nodes)} nodes | "
          f"speed: {min(n['processing_speed'] for n in base_nodes):.2f}–"
          f"{max(n['processing_speed'] for n in base_nodes):.2f} u/s\n")
    
    print("[setup] Computing MECT baseline for fitness normalisation...")
    mect_sched              = MECTScheduler()
    mect_df, mect_tpn       = run_simulation(workload, mect_sched, base_nodes, rng=rng)
    mect_metrics            = compute_metrics(mect_df, mect_tpn, base_nodes)
    set_baselines(
        avg_ct       = mect_metrics["avg_completion_time"],
        load_variance= mect_metrics["load_variance"],
        failure_rate = max(mect_metrics["failure_rate"], 1e-6),
        makespan     = mect_metrics["makespan"],
    )
    print(f"[setup] Baselines — AvgCT={mect_metrics['avg_completion_time']:.4f} | "
          f"LoadVar={mect_metrics['load_variance']:.2f} | "
          f"FailRate={mect_metrics['failure_rate']:.4f} | "
          f"Makespan={mect_metrics['makespan']:.4f}")
    
    optimizers = {
        "GA" : GeneticAlgorithm(seed=RNG_SEED),
        "PSO": PSO(seed=RNG_SEED+1),
        "DE" : DifferentialEvolution(seed=RNG_SEED+2),
    }
    
    opt_results = {}
    for name, opt in optimizers.items():
        print(f"\n{'─'*60}")
        print(f"  Running {name} ...")
        print(f"{'─'*60}")
        t0              = time.perf_counter()
        result          = opt.run(verbose=True)
        elapsed         = time.perf_counter() - t0
        result["time"]  = elapsed
        opt_results[name] = result
        print(f"  Wall time: {elapsed:.1f}s")
        
    print(f"\n{'='*68}")
    print("  EVALUATING OPTIMIZED SCHEDULERS")
    print(f"{'='*68}")
 
    policy_metrics = {}
    for name, result in opt_results.items():
        metrics = evaluate_policy(
            result["best_weights"], workload, base_nodes, rng
        )
        policy_metrics[f"Policy-{name}"] = metrics
        print(f"\n  Policy-{name} (fitness={result['best_fitness']:.6f})")
        print(f"    Weights : {np.round(result['best_weights'], 4).tolist()}")
        for k, v in metrics.items():
            if v is not None:
                print(f"    {k:<28s}: {v:.4f}")
    
    print(f"\n{'─'*68}")
    print("  BASELINE COMPARISON")
    print(f"{'─'*68}")
 
    baselines = {
        "Round Robin"  : RoundRobinScheduler(),
        "Least Loaded" : LeastLoadedScheduler(),
        "MECT"         : MECTScheduler(),
    }
    baseline_metrics = {}
    for name, sched in baselines.items():
        df, tpn = run_simulation(workload, sched, base_nodes, rng=rng)
        baseline_metrics[name] = compute_metrics(df, tpn, base_nodes)
        
    all_metrics = {**baseline_metrics, **policy_metrics}
    
    print(f"\n{'─'*68}")
    print("  FULL COMPARISON TABLE")
    print(f"{'─'*68}")
    metrics_df = build_metrics_table(all_metrics)
    print(metrics_df.to_string())
    
    mect_avg = baseline_metrics["MECT"]["avg_completion_time"]
    mect_slr = baseline_metrics["MECT"]["slr"]
    rr_slr   = baseline_metrics["Round Robin"]["slr"]
    
    print(f"\n{'─'*68}")
    print("  IMPROVEMENT OVER MECT BASELINE")
    print(f"{'─'*68}")
    print(f"  {'Optimizer':<15} {'AvgCT':>10} {'Improv%':>10} "
          f"{'SLR':>10} {'SLR Improv%':>12}")
    print(f"  {'─'*58}")
    for name in ["GA", "PSO", "DE"]:
        m       = policy_metrics[f"Policy-{name}"]
        avg_imp = (mect_avg - m["avg_completion_time"]) / mect_avg * 100
        slr_imp = (mect_slr - m["slr"]) / mect_slr * 100 if mect_slr else 0
        print(f"  {name:<15} "
              f"{m['avg_completion_time']:>10.4f} "
              f"{avg_imp:>+10.2f}% "
              f"{m['slr']:>10.4f} "
              f"{slr_imp:>+12.2f}%")
        
    rr_slr_val = baseline_metrics["Round Robin"]["slr"]
    print(f"\n  SLR improvement over Round Robin (target: >78.2%):")
    for name in ["GA", "PSO", "DE"]:
        m       = policy_metrics[f"Policy-{name}"]
        slr_imp = (rr_slr_val - m["slr"]) / rr_slr_val * 100 if rr_slr_val else 0
        print(f"    Policy-{name}: {slr_imp:+.2f}%")
        
    os.makedirs(CSV_DIR,   exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)
    
    out_csv = os.path.join(CSV_DIR, "metaheuristic_metrics.csv")
    metrics_df.to_csv(out_csv)
    
    weights_rows = []
    for name, result in opt_results.items():
        row = {"optimizer": name, "fitness": result["best_fitness"],
               "time_sec": round(result["time"], 2)}
        for i, w in enumerate(result["best_weights"]):
            row[f"w{i+1}"] = round(float(w), 6)
        weights_rows.append(row)
    weights_df = pd.DataFrame(weights_rows)
    out_weights = os.path.join(CSV_DIR, "metaheuristic_weights.csv")
    weights_df.to_csv(out_weights, index=False)
    
    for name, result in opt_results.items():
        hist_df  = pd.DataFrame({"generation": range(1, len(result["best_fitness_history"]) + 1),
                                  "best_fitness": result["best_fitness_history"]})
        hist_path = os.path.join(CSV_DIR, f"phase2_convergence_{name.lower()}.csv")
        hist_df.to_csv(hist_path, index=False)
 
    _plot_results(opt_results, all_metrics, baseline_metrics, policy_metrics,
                  base_nodes, PLOTS_DIR)
 
    return opt_results, all_metrics

def _plot_results(opt_results, all_metrics, baseline_metrics,
                  policy_metrics, base_nodes, plots_dir):
    """Generate Phase-2 comparison and convergence plots."""
 
    colors_opt  = {"GA": "#E74C3C", "PSO": "#2ECC71", "DE": "#3498DB"}
    colors_base = {"Round Robin": "#95A5A6", "Least Loaded": "#F39C12",
                   "MECT": "#8E44AD"}
 
    fig = plt.figure(figsize=(20, 16))
    fig.suptitle(
        "Phase-2: Metaheuristic Optimization of PolicyScheduler\n"
        "GA vs PSO vs DE — Dynamic Heterogeneous Distributed System",
        fontsize=14, fontweight="bold", y=0.98
    )
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)
 
    def style(ax, title, xlabel, ylabel):
        ax.set_title(title, fontweight="bold", fontsize=11)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(linestyle="--", alpha=0.4)
        
    ax1 = fig.add_subplot(gs[0, 0])
    for name, result in opt_results.items():
        ax1.plot(range(1, len(result["best_fitness_history"]) + 1),
                 result["best_fitness_history"],
                 color=colors_opt[name], linewidth=2, label=name)
    style(ax1, "Convergence Curves", "Generation / Iteration", "Best Fitness")
    ax1.legend(fontsize=9)
    
    ax2    = fig.add_subplot(gs[0, 1])
    names  = list(all_metrics.keys())
    avgs   = [all_metrics[n]["avg_completion_time"] for n in names]
    colors = []
    for n in names:
        if "GA" in n:      colors.append(colors_opt["GA"])
        elif "PSO" in n:   colors.append(colors_opt["PSO"])
        elif "DE" in n:    colors.append(colors_opt["DE"])
        elif "Robin" in n: colors.append(colors_base["Round Robin"])
        elif "Least" in n: colors.append(colors_base["Least Loaded"])
        else:              colors.append(colors_base["MECT"])
    bars = ax2.bar(range(len(names)), avgs, color=colors, edgecolor="white")
    ax2.bar_label(bars, fmt="%.3f", padding=2, fontsize=8)
    ax2.set_xticks(range(len(names)))
    ax2.set_xticklabels([n.replace("Policy-", "") for n in names],
                         rotation=30, ha="right", fontsize=8)
    style(ax2, "Avg Completion Time", "Scheduler", "Seconds")
    
    ax3  = fig.add_subplot(gs[0, 2])
    slrs = [all_metrics[n]["slr"] for n in names]
    bars = ax3.bar(range(len(names)), slrs, color=colors, edgecolor="white")
    ax3.bar_label(bars, fmt="%.4f", padding=2, fontsize=8)
    ax3.set_xticks(range(len(names)))
    ax3.set_xticklabels([n.replace("Policy-", "") for n in names],
                         rotation=30, ha="right", fontsize=8)
    style(ax3, "Scheduling Length Ratio (SLR)", "Scheduler", "SLR")
 
    ax4        = fig.add_subplot(gs[1, 0])
    w_labels   = ["w1\nSpeed", "w2\nQueue", "w3\nLatency",
                  "w4\nFailure", "w5\nCapacity", "w6\nCost"]
    x          = np.arange(len(w_labels))
    bar_width  = 0.25
    for idx, (name, result) in enumerate(opt_results.items()):
        ax4.bar(x + idx * bar_width, result["best_weights"], bar_width,
                label=name, color=colors_opt[name], edgecolor="white", alpha=0.85)
    ax4.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax4.set_xticks(x + bar_width)
    ax4.set_xticklabels(w_labels, fontsize=8)
    style(ax4, "Optimized Weight Vectors", "Weight", "Value")
    ax4.legend(fontsize=9)
    
    ax5       = fig.add_subplot(gs[1, 1])
    fail_vals = [all_metrics[n]["failure_rate"] * 100 for n in names]
    bars      = ax5.bar(range(len(names)), fail_vals, color=colors, edgecolor="white")
    ax5.bar_label(bars, fmt="%.2f%%", padding=2, fontsize=8)
    ax5.set_xticks(range(len(names)))
    ax5.set_xticklabels([n.replace("Policy-", "") for n in names],
                         rotation=30, ha="right", fontsize=8)
    style(ax5, "Task Failure Rate (%)", "Scheduler", "Failure Rate (%)")
    
    ax6      = fig.add_subplot(gs[1, 2])
    p95_vals = [all_metrics[n]["p95_latency"] for n in names]
    bars     = ax6.bar(range(len(names)), p95_vals, color=colors, edgecolor="white")
    ax6.bar_label(bars, fmt="%.3f", padding=2, fontsize=8)
    ax6.set_xticks(range(len(names)))
    ax6.set_xticklabels([n.replace("Policy-", "") for n in names],
                         rotation=30, ha="right", fontsize=8)
    style(ax6, "95th Percentile Latency", "Scheduler", "P95 (s)")
 
    out_path = os.path.join(plots_dir, "metaheuristic_results.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
if __name__ == "__main__":
    run_optimizer_experiment()
 