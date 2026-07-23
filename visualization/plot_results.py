import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


COLORS = ["#4C72B0", "#55A868", "#C44E52"]


def plot_results(
    all_results:  dict,
    all_metrics:  dict,
    all_per_node: dict,
    save_dir:     str = "results/plots",
) -> None:
    os.makedirs(save_dir, exist_ok=True)

    names   = list(all_metrics.keys())
    n_nodes = len(next(iter(all_per_node.values())))

    fig = plt.figure(figsize=(18, 14))
    fig.suptitle(
        "Phase-1 Baseline Evaluation — Heuristic Schedulers in a\n"
        "Dynamic Heterogeneous Distributed Computing Environment",
        fontsize=14, fontweight="bold", y=0.98,
    )
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, 0])
    avg_cts = [all_metrics[n]["avg_completion_time"] for n in names]
    bars = ax1.bar(names, avg_cts, color=COLORS, edgecolor="black", width=0.5)
    ax1.bar_label(bars, fmt="%.3f", padding=3, fontsize=9)
    ax1.set_title("Avg Task Completion Time", fontweight="bold")
    ax1.set_ylabel("Seconds")
    ax1.set_ylim(0, max(avg_cts) * 1.25)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    ax2 = fig.add_subplot(gs[0, 1])
    p95s = [all_metrics[n]["p95_latency"] for n in names]
    bars = ax2.bar(names, p95s, color=COLORS, edgecolor="black", width=0.5)
    ax2.bar_label(bars, fmt="%.3f", padding=3, fontsize=9)
    ax2.set_title("95th Percentile (Tail) Latency", fontweight="bold")
    ax2.set_ylabel("Seconds")
    ax2.set_ylim(0, max(p95s) * 1.25)
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    ax3    = fig.add_subplot(gs[0, 2])
    x      = np.arange(n_nodes)
    width  = 0.25
    for i, (name, color) in enumerate(zip(names, COLORS)):
        ax3.bar(x + i * width, all_per_node[name], width,
                label=name, color=color, edgecolor="black", alpha=0.85)
    ax3.set_title("Node Load Distribution\n(Tasks Handled per Node)", fontweight="bold")
    ax3.set_xlabel("Node ID")
    ax3.set_ylabel("Tasks Handled")
    ax3.set_xticks(x + width)
    ax3.set_xticklabels([f"N{i}" for i in range(n_nodes)], fontsize=7)
    ax3.legend(fontsize=8)
    ax3.grid(axis="y", linestyle="--", alpha=0.5)

    ax4 = fig.add_subplot(gs[1, 0:2])
    for name, color in zip(names, COLORS):
        ct_vals = all_results[name]["completion_time"].dropna()
        ax4.hist(ct_vals, bins=40, density=True, alpha=0.45,
                 color=color, edgecolor="none", label=name)
        sorted_ct = np.sort(ct_vals)
        mu, sigma = sorted_ct.mean(), sorted_ct.std()
        if sigma > 0:
            gaussian = (np.exp(-0.5 * ((sorted_ct - mu) / sigma) ** 2)
                        / (sigma * np.sqrt(2 * np.pi)))
            ax4.plot(sorted_ct, gaussian, color=color, linewidth=2)
    ax4.set_title("Task Completion Time Distribution", fontweight="bold")
    ax4.set_xlabel("Completion Time (s)")
    ax4.set_ylabel("Density")
    ax4.legend(fontsize=9)
    ax4.grid(linestyle="--", alpha=0.4)

    ax5 = fig.add_subplot(gs[1, 2])
    metric_labels = ["Load\nVariance", "Failure\nRate", "Throughput\n(norm)"]
    raw = {
        "Load\nVariance":    [all_metrics[n]["load_variance"]  for n in names],
        "Failure\nRate":     [all_metrics[n]["failure_rate"]   for n in names],
        "Throughput\n(norm)":[all_metrics[n]["throughput"]     for n in names],
    }
    norm = {}
    for k, vals in raw.items():
        mn, mx   = min(vals), max(vals)
        span_v   = mx - mn if mx != mn else 1.0
        norm[k]  = [(v - mn) / span_v for v in vals]

    x2     = np.arange(len(metric_labels))
    width2 = 0.25
    for i, (name, color) in enumerate(zip(names, COLORS)):
        vals_norm = [norm[ml][i] for ml in metric_labels]
        ax5.bar(x2 + i * width2, vals_norm, width2,
                label=name, color=color, edgecolor="black", alpha=0.85)
    ax5.set_title(
        "Normalised Secondary Metrics\n(lower = better for var/fail, higher for tput)",
        fontweight="bold", fontsize=9,
    )
    ax5.set_xticks(x2 + width2)
    ax5.set_xticklabels(metric_labels, fontsize=8)
    ax5.set_ylabel("Normalised Score")
    ax5.legend(fontsize=8)
    ax5.grid(axis="y", linestyle="--", alpha=0.5)

    out_path = os.path.join(save_dir, "baseline_results.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


