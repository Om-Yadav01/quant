import os
import sys
import time
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import matplotlib.cm as cm

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
from optimizers.hybrid_cce_optimizer import HybridCCEOptimizer
from evaluation.fitness import evaluate_weights, set_baselines, set_workload_cache, N_WEIGHTS

RNG_SEED  = 42
N_TASKS   = 1000
N_NODES   = 15

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR   = os.path.join(_PROJECT_ROOT, "results", "csv")
PLOTS_DIR = os.path.join(_PROJECT_ROOT, "results", "plots")

COLORS = {
    "Round Robin"  : "#95A5A6",
    "Least Loaded" : "#F39C12",
    "MECT"         : "#8E44AD",
    "GA"           : "#E74C3C",
    "PSO"          : "#2ECC71",
    "DE"           : "#3498DB",
    "Hybrid CCE"   : "#E67E22",
}
 
WEIGHT_LABELS = ["w1\nSpeed", "w2\nQueue", "w3\nLatency",
                 "w4\nFailure", "w5\nCapacity", "w6\nCost"]

def evaluate_policy(weights, workload, base_nodes, rng):
    scheduler          = PolicyScheduler(weights)
    df, tasks_per_node = run_simulation(workload, scheduler, base_nodes, rng=rng)
    return compute_metrics(df, tasks_per_node, base_nodes)
 
 
def run_baselines(workload, base_nodes, rng):
    schedulers = {
        "Round Robin" : RoundRobinScheduler(),
        "Least Loaded": LeastLoadedScheduler(),
        "MECT"        : MECTScheduler(),
    }
    metrics = {}
    for name, sched in schedulers.items():
        df, tpn      = run_simulation(workload, sched, base_nodes, rng=rng)
        metrics[name] = compute_metrics(df, tpn, base_nodes)
    return metrics

def run_hybrid_experiment():
    print("=" * 68)
 
    rng        = np.random.default_rng(RNG_SEED)
    workload   = get_workload(N_TASKS, rng=rng)
    base_nodes = build_cluster(N_NODES, rng=rng)
    set_workload_cache(workload, base_nodes)
 
    print(f"\n[Workload] {len(workload)} tasks | "
          f"arrival window: {workload.arrival_time.max():.1f}s")
    print(f"[Cluster]  {len(base_nodes)} nodes | "
          f"speed: {min(n['processing_speed'] for n in base_nodes):.2f}–"
          f"{max(n['processing_speed'] for n in base_nodes):.2f} u/s")
 
    print("\n[setup] Computing MECT baseline for fitness normalisation...")
    mect_sched        = MECTScheduler()
    mect_df, mect_tpn = run_simulation(workload, mect_sched, base_nodes, rng=rng)
    mect_m            = compute_metrics(mect_df, mect_tpn, base_nodes)
    set_baselines(
        avg_ct        = mect_m["avg_completion_time"],
        load_variance = mect_m["load_variance"],
        failure_rate  = max(mect_m["failure_rate"], 1e-6),
        makespan      = mect_m["makespan"],
    )
    print(f"[setup] Baselines — AvgCT={mect_m['avg_completion_time']:.4f} | "
          f"LoadVar={mect_m['load_variance']:.2f} | "
          f"FailRate={mect_m['failure_rate']:.4f} | "
          f"Makespan={mect_m['makespan']:.4f}")
    
    optimizers = {
        "GA"        : GeneticAlgorithm(seed=RNG_SEED),
        "PSO"       : PSO(seed=RNG_SEED + 1),
        "DE"        : DifferentialEvolution(seed=RNG_SEED + 2),
        "Hybrid CCE": HybridCCEOptimizer(seed=RNG_SEED + 3),
    }
 
    opt_results = {}
    for name, opt in optimizers.items():
        print(f"\n{'─'*60}\n  Running {name} ...\n{'─'*60}")
        t0             = time.perf_counter()
        result         = opt.run(verbose=True)
        result["time"] = time.perf_counter() - t0
        opt_results[name] = result
        print(f"  Wall time: {result['time']:.1f}s")
        
    print(f"\n{'='*68}\n  EVALUATING OPTIMIZED SCHEDULERS\n{'='*68}")
    policy_metrics = {}
    for name, result in opt_results.items():
        m = evaluate_policy(result["best_weights"], workload, base_nodes, rng)
        policy_metrics[f"Policy-{name}"] = m
        print(f"\n  Policy-{name}  (fitness={result['best_fitness']:.6f}  "
              f"time={result['time']:.1f}s)")
        print(f"    Weights : {np.round(result['best_weights'], 4).tolist()}")
        for k, v in m.items():
            if v is not None:
                print(f"    {k:<28s}: {v:.4f}")
    
    print(f"\n{'─'*68}\n  BASELINE COMPARISON\n{'─'*68}")
    baseline_metrics = run_baselines(workload, base_nodes, rng)
 
    all_metrics = {**baseline_metrics, **policy_metrics}
    print(f"\n{'─'*68}\n  FULL COMPARISON TABLE\n{'─'*68}")
    metrics_df = build_metrics_table(all_metrics)
    print(metrics_df.to_string())
 
    mect_avg = baseline_metrics["MECT"]["avg_completion_time"]
    rr_slr   = baseline_metrics["Round Robin"]["slr"]
 
    print(f"\n{'─'*68}\n  IMPROVEMENT OVER MECT\n{'─'*68}")
    print(f"  {'Optimizer':<12} {'AvgCT':>8} {'Δ%':>8} "
          f"{'P95':>8} {'Δ%':>8}     "
          f"{'Makespan':>10} {'Δ%':>8} "
          f"{'FailRate':>10} {'Δ%':>8}")
    print(f"  {'─'*80}")
 
    mect_p95  = baseline_metrics["MECT"]["p95_latency"]
    mect_ms   = baseline_metrics["MECT"]["makespan"]
    mect_fr   = baseline_metrics["MECT"]["failure_rate"]
    
    improvement_rows = []
    for opt_name in ["GA", "PSO", "DE", "Hybrid CCE"]:
        m   = policy_metrics[f"Policy-{opt_name}"]
        d_avg = (mect_avg - m["avg_completion_time"]) / mect_avg * 100
        d_p95 = (mect_p95 - m["p95_latency"])         / mect_p95 * 100
        d_ms  = (mect_ms  - m["makespan"])             / mect_ms  * 100
        d_fr  = (mect_fr  - m["failure_rate"])         / max(mect_fr, 1e-9) * 100
        print(f"  {opt_name:<12} "
              f"{m['avg_completion_time']:>8.4f} {d_avg:>+8.2f}% "
              f"{m['p95_latency']:>8.4f} {d_p95:>+8.2f}% "
              f"{m['makespan']:>10.4f} {d_ms:>+8.2f}% "
              f"{m['failure_rate']:>10.4f} {d_fr:>+8.2f}%")
        improvement_rows.append({
            "optimizer"        : opt_name,
            "avg_ct"           : m["avg_completion_time"],
            "avg_ct_improv"    : d_avg,
            "p95"              : m["p95_latency"],
            "p95_improv"       : d_p95,
            "makespan"         : m["makespan"],
            "makespan_improv"  : d_ms,
            "failure_rate"     : m["failure_rate"],
            "failure_improv"   : d_fr,
            "slr"              : m["slr"],
            "fitness"          : opt_results[opt_name]["best_fitness"],
            "time_sec"         : opt_results[opt_name]["time"],
        })
    
    print(f"\n  SLR improvement over Round Robin (paper target: >78.2%):")
    for opt_name in ["GA", "PSO", "DE", "Hybrid CCE"]:
        m       = policy_metrics[f"Policy-{opt_name}"]
        slr_imp = (rr_slr - m["slr"]) / rr_slr * 100 if rr_slr else 0
        print(f"    Policy-{opt_name:<12}: {slr_imp:+.2f}%")
 
    os.makedirs(CSV_DIR,   exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)
 
    metrics_df.to_csv(os.path.join(CSV_DIR, "phase2_full_comparison.csv"))
    pd.DataFrame(improvement_rows).to_csv(
        os.path.join(CSV_DIR, "phase2_improvement_report.csv"), index=False
    )
    for name, result in opt_results.items():
        slug = name.lower().replace(" ", "_")
        pd.DataFrame({
            "iteration"   : range(1, len(result["best_fitness_history"]) + 1),
            "best_fitness": result["best_fitness_history"],
        }).to_csv(os.path.join(CSV_DIR, f"phase2_convergence_{slug}.csv"),
                  index=False)
                  
    rows = []
    for name, result in opt_results.items():
        row = {"optimizer": name, "fitness": result["best_fitness"]}
        for i, w in enumerate(result["best_weights"]):
            row[f"w{i+1}"] = round(float(w), 6)
        rows.append(row)
    pd.DataFrame(rows).to_csv(
        os.path.join(CSV_DIR, "phase2_best_weights.csv"), index=False
    )
    print(f"\n[✓] All CSVs saved → {CSV_DIR}")
 
    _generate_plots(opt_results, all_metrics, baseline_metrics,
                    policy_metrics, improvement_rows)
 
    return opt_results, all_metrics, improvement_rows

def _generate_plots(opt_results, all_metrics, baseline_metrics,
                    policy_metrics, improvement_rows):
 
    os.makedirs(PLOTS_DIR, exist_ok=True)
 
    fig1, ax = plt.subplots(figsize=(10, 6))
    for name, result in opt_results.items():
        hist = result["best_fitness_history"]
        ax.plot(range(1, len(hist) + 1), hist,
                color=COLORS[name], linewidth=2.2,
                label=name, marker="o", markevery=10, markersize=5)
    ax.set_title("Convergence Curves — All Optimizers",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Iteration / Generation", fontsize=12)
    ax.set_ylabel("Best Fitness (normalised)", fontsize=12)
    ax.legend(fontsize=11, framealpha=0.9)
    ax.grid(linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=1.5,
               label="MECT baseline")
    ax.legend(fontsize=11, framealpha=0.9)
    plt.tight_layout()
    fig1.savefig(os.path.join(PLOTS_DIR, "convergence_curves.png"),
                 dpi=150, bbox_inches="tight")
    plt.close(fig1)
    
    if "Hybrid CCE" in opt_results:
        fig2, ax = plt.subplots(figsize=(10, 6))
        cce_hist  = opt_results["Hybrid CCE"]["best_fitness_history"]
        sub_hist  = opt_results["Hybrid CCE"].get("subgroup_history", {})
        ax.plot(range(1, len(cce_hist) + 1), cce_hist,
                color=COLORS["Hybrid CCE"], linewidth=2.5,
                label="CCE Global Best", zorder=5)
        sub_colors = {"DE": COLORS["DE"], "PSO": COLORS["PSO"], "GA": COLORS["GA"]}
        for sub_name, sub_c in sub_colors.items():
            if sub_name in sub_hist and sub_hist[sub_name]:
                ax.plot(range(1, len(sub_hist[sub_name]) + 1),
                        sub_hist[sub_name],
                        color=sub_c, linewidth=1.5, linestyle="--",
                        alpha=0.75, label=f"Sub-group {sub_name}")
        ax.axhline(1.0, color="gray", linestyle=":", linewidth=1.5,
                   label="MECT baseline")
        ax.set_title("CCE Sub-Group Convergence\n"
                     "DE(w1,w5) | PSO(w2,w3) | GA(w4,w6)",
                     fontsize=14, fontweight="bold")
        ax.set_xlabel("Iteration", fontsize=12)
        ax.set_ylabel("Best Fitness (normalised)", fontsize=12)
        ax.legend(fontsize=10, framealpha=0.9)
        ax.grid(linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        fig2.savefig(os.path.join(PLOTS_DIR, "cce_subgroup_convergence.png"),
                     dpi=150, bbox_inches="tight")
        plt.close(fig2)

    scheduler_order = ["Round Robin", "Least Loaded", "MECT",
                       "Policy-GA", "Policy-PSO", "Policy-DE", "Policy-Hybrid CCE"]
    scheduler_order = [s for s in scheduler_order if s in all_metrics]
    short_names = [s.replace("Policy-", "") for s in scheduler_order]
 
    bar_colors = []
    for s in scheduler_order:
        key = s.replace("Policy-", "")
        bar_colors.append(COLORS.get(key, "#7F8C8D"))
 
    fig3, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig3.suptitle("Scheduler Performance Comparison\n"
                  "Baselines vs Metaheuristic Optimizers",
                  fontsize=14, fontweight="bold", y=1.01)
 
    metrics_to_plot = [
        ("avg_completion_time", "Avg Completion Time (s)",    axes[0, 0]),
        ("p95_latency",         "P95 Latency (s)",            axes[0, 1]),
        ("makespan",            "Makespan (s)",                axes[1, 0]),
        ("failure_rate",        "Failure Rate",                axes[1, 1]),
    ]
    
    for metric_key, ylabel, ax in metrics_to_plot:
        vals = [all_metrics[s][metric_key] for s in scheduler_order]
        bars = ax.bar(range(len(scheduler_order)), vals,
                      color=bar_colors, edgecolor="white", linewidth=1.2)
        ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=7.5)
        ax.set_xticks(range(len(scheduler_order)))
        ax.set_xticklabels(short_names, rotation=25, ha="right", fontsize=9)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        mect_idx = scheduler_order.index("MECT")
        ax.get_children()[mect_idx].set_edgecolor("black")
        ax.get_children()[mect_idx].set_linewidth(2)
 
    plt.tight_layout()
    fig3.savefig(os.path.join(PLOTS_DIR, "scheduler_comparison.png"),
                 dpi=150, bbox_inches="tight")
    plt.close(fig3)
    
    fig4, ax = plt.subplots(figsize=(10, 5))
    slr_vals = [all_metrics[s]["slr"] for s in scheduler_order]
    bars     = ax.bar(range(len(scheduler_order)), slr_vals,
                      color=bar_colors, edgecolor="white", linewidth=1.2)
    ax.bar_label(bars, fmt="%.4f", padding=2, fontsize=9)
    ax.set_xticks(range(len(scheduler_order)))
    ax.set_xticklabels(short_names, rotation=20, ha="right", fontsize=10)
    ax.set_ylabel("Scheduling Length Ratio (SLR)", fontsize=11)
    ax.set_title("SLR Comparison — All Schedulers\n"
                 "(Lower is better; Li & Chen 2024 target: SLR < 13.7 relative)",
                 fontsize=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig4.savefig(os.path.join(PLOTS_DIR, "slr_comparison.png"),
                 dpi=150, bbox_inches="tight")
    plt.close(fig4)
    
    opt_names  = list(opt_results.keys())
    weight_mat = np.array([opt_results[n]["best_weights"] for n in opt_names])
 
    fig5, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(weight_mat, cmap="RdYlGn", aspect="auto",
                   vmin=-5, vmax=5)
    plt.colorbar(im, ax=ax, label="Weight Value")
    ax.set_xticks(range(6))
    ax.set_xticklabels(WEIGHT_LABELS, fontsize=11)
    ax.set_yticks(range(len(opt_names)))
    ax.set_yticklabels(opt_names, fontsize=11)
    ax.set_title("Learned Weight Vectors — All Optimizers\n"
                 "(Green = high positive, Red = high negative)",
                 fontsize=12, fontweight="bold")
    for i in range(len(opt_names)):
        for j in range(6):
            ax.text(j, i, f"{weight_mat[i, j]:.2f}",
                    ha="center", va="center", fontsize=9,
                    color="black")
    plt.tight_layout()
    fig5.savefig(os.path.join(PLOTS_DIR, "weight_vectors_heatmap.png"),
                 dpi=150, bbox_inches="tight")
    plt.close(fig5)
    
    if improvement_rows:
        imp_df    = pd.DataFrame(improvement_rows)
        imp_names = imp_df["optimizer"].tolist()
        metrics_imp = [
            ("avg_ct_improv",   "Avg CT",     "#3498DB"),
            ("p95_improv",      "P95 Latency","#2ECC71"),
            ("makespan_improv", "Makespan",   "#E74C3C"),
            ("failure_improv",  "Failure Rate","#F39C12"),
        ]
        x      = np.arange(len(imp_names))
        width  = 0.2
        fig6, ax = plt.subplots(figsize=(11, 6))
        for idx, (col, label, color) in enumerate(metrics_imp):
            vals = imp_df[col].tolist()
            bars = ax.bar(x + idx * width, vals, width,
                          label=label, color=color, edgecolor="white", alpha=0.9)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(imp_names, fontsize=11)
        ax.set_ylabel("Improvement over MECT (%)", fontsize=11)
        ax.set_title("Percentage Improvement over MECT Baseline\n"
                     "Positive = better than MECT",
                     fontsize=12, fontweight="bold")
        ax.legend(fontsize=10, framealpha=0.9)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        fig6.savefig(os.path.join(PLOTS_DIR, "improvement_over_mect.png"),
                     dpi=150, bbox_inches="tight")
        plt.close(fig6)
        
    radar_metrics  = ["avg_completion_time", "p95_latency", "makespan",
                      "failure_rate", "slr"]
    radar_labels   = ["Avg CT", "P95", "Makespan", "Fail Rate", "SLR"]
    radar_subjects = ["MECT", "Policy-GA", "Policy-PSO",
                      "Policy-DE", "Policy-Hybrid CCE"]
    radar_subjects = [s for s in radar_subjects if s in all_metrics]
 
    raw_vals = np.array([[all_metrics[s][m] for m in radar_metrics]
                         for s in radar_subjects])
    col_min  = raw_vals.min(axis=0)
    col_max  = raw_vals.max(axis=0)
    col_span = np.where(col_max - col_min < 1e-9, 1.0, col_max - col_min)
    norm_vals = (raw_vals - col_min) / col_span
 
    norm_vals = 1.0 - norm_vals
 
    N       = len(radar_labels)
    angles  = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
 
    fig7, ax = plt.subplots(figsize=(8, 8),
                             subplot_kw=dict(polar=True))
    radar_colors = [COLORS["MECT"], COLORS["GA"], COLORS["PSO"],
                    COLORS["DE"], COLORS["Hybrid CCE"]]

    for idx, (subj, color) in enumerate(zip(radar_subjects, radar_colors)):
        vals  = norm_vals[idx].tolist() + [norm_vals[idx][0]]
        label = subj.replace("Policy-", "")
        ax.plot(angles, vals, color=color, linewidth=2, label=label)
        ax.fill(angles, vals, color=color, alpha=0.08)
 
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(radar_labels, fontsize=11)
    ax.set_title("Multi-Metric Radar Profile\n"
                 "(Outward = better performance)",
                 fontsize=12, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=10)
    plt.tight_layout()
    fig7.savefig(os.path.join(PLOTS_DIR, "radar_profile.png"),
                 dpi=150, bbox_inches="tight")
    plt.close(fig7)
    
    fig8, ax = plt.subplots(figsize=(8, 5))
    times    = [opt_results[n]["time"] for n in opt_results]
    fits     = [opt_results[n]["best_fitness"] for n in opt_results]
    names    = list(opt_results.keys())
    colors8  = [COLORS[n] for n in names]
    sc = ax.scatter(times, fits, c=colors8, s=200, zorder=5, edgecolors="white",
                    linewidth=1.5)
    for i, name in enumerate(names):
        ax.annotate(name, (times[i], fits[i]),
                    textcoords="offset points", xytext=(8, 4), fontsize=10)
    ax.set_xlabel("Wall Time (seconds)", fontsize=11)
    ax.set_ylabel("Best Fitness (normalised)", fontsize=11)
    ax.set_title("Runtime vs Best Fitness — Efficiency Trade-off\n"
                 "(Bottom-left = faster and better)",
                 fontsize=12, fontweight="bold")
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=1.5,
               label="MECT baseline")
    ax.legend(fontsize=10)
    ax.grid(linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig8.savefig(os.path.join(PLOTS_DIR, "runtime_vs_fitness.png"),
                 dpi=150, bbox_inches="tight")
    plt.close(fig8)

if __name__ == "__main__":
    run_hybrid_experiment()
    
