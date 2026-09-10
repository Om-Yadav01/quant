# BIGAPI Publisher Revision Plan

Scope note: the attached PDF was reviewed as source material only. The repository contains code and documentation, but it does not contain the editable manuscript source (`.docx`, `.tex`, or figures). This plan records the required manuscript edits and the code changes made to support Reviewer #3's technical concerns.

## Revision Status

| Area | Status | Repository support |
| --- | --- | --- |
| Local environment | Done | `.venv` created locally; setup commands added to `README.md` |
| Six-objective fitness | Done | `evaluation/fitness.py` now optimizes AvgCT, P95, makespan, load variance, failure rate, and SLR |
| Penalty-weight sign issue | Done | Optimizer search bounds changed from `[-5, 5]` to `[0, 5]` |
| SLR definition | Done | `evaluation/metrics.py` now uses a parallel lower bound and reports `slr_lower_bound` |
| Baseline consistency | Done | Experiments now call `set_baselines_from_metrics()` and print all normalization constants |
| Robustness testing | Done | `experiments/robustness_experiment.py` added |
| Coefficient sensitivity | Done | `experiments/sensitivity_analysis.py` added |
| Editable manuscript/Word upload | Blocked until source file is supplied | Only the PDF is available; do not convert blindly for final submission |
| English proofreading | Pending human/service proofread | Recommended by reviewers and editor |
| ORCID | Pending author input | Add at least one author ORCID in the manuscript metadata/title page |

## Reviewer #1 Response Matrix

| Comment | Required manuscript action | Implementation/documentation action |
| --- | --- | --- |
| English needs proofreading | Send the final `.docx` through a native English proofreader or one of the publisher-suggested services. | Track as a submission checklist item. |
| Abstract must include Objectives, Methods/Analysis, Findings, Novelty/Improvement in one approximately 200-word paragraph | Replace the abstract with the draft below after inserting final rerun values. | Draft provided in this document. |
| Introduction is poorly written and lacks literature gap | Rewrite the introduction around dynamic heterogeneity, multi-objective scheduling, workload realism, and the gap in robust validation. | Recent references listed below. |
| Add recent 2025-2026 work | Add at least five new numbered references and cite them in the introduction/related work. | Six candidate references listed below. |
| Figure quality unacceptable | Regenerate figures using `results/plots` at high DPI and export editable source when possible. | Existing plot scripts save PNGs; revise manuscript figures after rerunning. |
| Results need more explanation | Expand per-metric discussion, especially trade-offs between AvgCT/P95, makespan, load variance, failures, and SLR. | Six-objective metrics now generated consistently. |
| Compare with previous studies | Compare qualitatively when definitions differ; do not claim a numerical SLR win against incompatible SLR definitions. | The old Li and Chen SLR comparison should be removed. |
| Rewrite conclusion to 300-350 words | Replace the conclusion with a fuller summary of findings, limitations, robustness, and future work. | Draft provided below. |
| Cite all charts and figures in main text | Every figure must be introduced before it appears and discussed after it appears. | Upload checklist includes figure citation audit. |
| Define all symbols and parameters | Add a notation table before or after the methodology. | Draft notation table provided below. |
| Number references sequentially | Convert all citations to journal style `[1]`, `[2]`, etc. | Upload checklist includes reference renumbering. |
| Journal format not followed | Move to journal Word template and check headings, captions, margins, author metadata, ORCID, and reference style. | Upload checklist covers this. |

## Reviewer #3 Response Matrix

| Comment | Response |
| --- | --- |
| Six objectives claimed but Equation (7) optimizes four | Revised fitness optimizes six normalized objectives: AvgCT, P95, makespan, load variance, failure rate, and SLR. |
| Coefficient rationale insufficient and makespan weight contradiction | Equation text should use the six-objective weights in `evaluation/fitness.py`: 0.25, 0.20, 0.20, 0.10, 0.15, 0.10. Run `experiments/sensitivity_analysis.py` and report sensitivity results. |
| MECT normalization values inconsistent | Use a single baseline table generated from `set_baselines_from_metrics()` and copy the same constants into the manuscript. |
| SLR denominator invalid under parallelism | SLR now uses the ratio between observed schedule length and an internal parallel lower bound, not the sum of fastest serial execution times. |
| Invalid comparison with Li and Chen | Remove the claim that the SLR improvement exceeds Li and Chen. Replace it with a qualitative comparison and state that SLR definitions are not directly comparable. |
| Negative weights reverse penalties | Search bounds are now `[0, 5]`; penalty features remain penalties because the scheduler formula already applies the negative sign. |
| Robustness over 1,000 sampled records, arrival windows, intensities, clusters | Added `experiments/robustness_experiment.py` to test repeated samples, 300/600/1200 second windows, light/heavy workloads, and different cluster sizes. |

## Revised Abstract Draft

Objectives: This study addresses dynamic task scheduling in heterogeneous distributed systems where task arrivals, queue states, node speeds, communication latency, and failures change over time. Methods/Analysis: We develop a policy-based scheduler whose six nonnegative weights guide node selection across processing speed, queue workload, network latency, failure probability, available capacity, and execution cost. The weights are optimized using Genetic Algorithm, Particle Swarm Optimization, Differential Evolution, and a Cooperative Co-Evolution Hybrid optimizer. Performance is evaluated against Round Robin, Least Loaded, and MECT baselines using average completion time, P95 latency, makespan, load variance, failure rate, throughput, and a revised Schedule Length Ratio based on a parallel lower bound. Findings: The optimized policies reduce average and tail completion delays relative to MECT while exposing interpretable trade-offs between latency, reliability, and load concentration. Sensitivity and robustness experiments across multiple samples, arrival windows, workload intensities, and cluster sizes are used to verify that the reported improvements are not artifacts of a single sampled trace. Novelty/Improvement: The work contributes a transparent six-objective scheduling formulation, constrained penalty weights that preserve feature semantics, a corrected SLR definition, and a cooperative optimizer design that balances latency-sensitive and reliability-sensitive scheduling behavior.

## Revised Conclusion Draft

This study presented a dynamic scheduling framework for heterogeneous distributed systems in which task assignment is controlled by an interpretable six-feature policy and optimized through evolutionary and cooperative co-evolutionary search. The revised formulation resolves the mismatch between the original six-objective claim and the four-term fitness function by explicitly incorporating average completion time, P95 latency, makespan, load variance, failure rate, and Schedule Length Ratio into a single normalized objective. The resulting policy search remains easy to interpret because each learned weight corresponds to a concrete scheduling feature, while the nonnegative weight bounds preserve the intended meaning of penalty terms for queue length, latency, failure probability, and execution cost. The corrected SLR metric also avoids an invalid serial denominator by comparing observed schedule length against a parallel lower bound derived from task releases, fastest feasible task durations, and aggregate cluster capacity.

The experimental workflow now supports a stronger evaluation protocol. Baseline constants are generated once from the MECT run and reused consistently across the optimizer fitness calculation, result tables, and manuscript text. Sensitivity analysis is added to justify the selected coefficient values, and robustness experiments vary random samples, arrival compression windows, workload intensity, and cluster size to test whether the conclusions survive changes in workload dynamics. The results should therefore be discussed as multi-metric trade-offs rather than as a single universal dominance claim: optimized policies may improve mean and tail latency by concentrating work on faster nodes, but that can increase load variance and sometimes affect makespan or reliability. Future work should evaluate larger trace samples, compare against directly comparable workflow benchmarks, add energy and cost measurements where data are available, and validate the policy in a real distributed testbed. Overall, the revised framework provides a reproducible and more methodologically defensible basis for studying adaptive task scheduling under heterogeneous and dynamic operating conditions.

## Notation And Parameter Definitions

| Symbol/parameter | Definition |
| --- | --- |
| `w1` | Processing-speed reward weight |
| `w2` | Queue-workload penalty weight |
| `w3` | Network-latency penalty weight |
| `w4` | Failure-probability penalty weight |
| `w5` | Available-capacity reward weight |
| `w6` | Execution-cost penalty weight |
| `W` | Six-dimensional policy weight vector |
| `Q_j(t)` | Queue workload on node `j` at time `t` |
| `s_j` | Processing speed of node `j` |
| `l_j` | Network latency of node `j` |
| `f_j` | Failure probability of node `j` |
| `CT` | Completion time/response time for a task |
| `P95` | 95th percentile completion time |
| `M` | Schedule makespan, measured from first task arrival to last task finish |
| `SLR` | Schedule Length Ratio, computed as `M / parallel_lower_bound` |
| `N_TASKS` | Number of sampled tasks in one experiment |
| `N_NODES` | Number of simulated heterogeneous nodes |
| `arrival_window` | Time window used to rescale sampled task arrivals |
| `workload_scale` | Multiplier applied to sampled workload sizes in robustness testing |

## Recent References To Add

Use the journal's required numbered style and renumber the full list sequentially.

[19] J. Aminu, R. Latip, Z. M. Hanafi, S. Kamarudin, and D. Gabi, "Systematic review of metaheuristic-based task scheduling strategies in edge computing environments," Discover Computing, vol. 28, article 307, 2025. https://doi.org/10.1007/s10791-025-09819-4

[20] A. B. Naeem, B. Senapati, J. Rasheed, J. Baili, and O. Osman, "An intelligent job scheduling and real-time resource optimization for edge-cloud continuum in next generation networks," Scientific Reports, vol. 15, article 41534, 2025. https://doi.org/10.1038/s41598-025-25452-z

[21] W. Zhang and H. Ou, "Reinforcement learning based multi objective task scheduling for energy efficient and cost effective cloud edge computing," Scientific Reports, vol. 15, article 41716, 2025. https://doi.org/10.1038/s41598-025-25666-1

[22] P. Sravan and M. A. Shaik, "DRL-based multi-objective task scheduling for edge-cloud computing: latency, energy, and SLA optimisation," Scientific Reports, vol. 16, article 19681, 2026. https://doi.org/10.1038/s41598-026-49824-1

[23] N. Yamsani et al., "SLA aware deep reinforcement learning for adaptive EdgeCloud task scheduling," Scientific Reports, vol. 16, article 10037, 2026. https://doi.org/10.1038/s41598-026-40237-8

[24] L. R. Raju et al., "IntelliScheduler: an edge-cloud computing environment hybrid deep learning framework for task scheduling based on learning," Scientific Reports, vol. 16, article 11219, 2026. https://doi.org/10.1038/s41598-026-41330-8

## Manuscript Edits Still Required

1. Replace Equation (7) with the six-objective fitness function and list the six coefficients exactly as implemented.
2. Replace Equation (8) with the revised SLR definition using the parallel lower bound.
3. Remove the numerical comparison claiming superiority over Li and Chen's SLR benchmark unless a directly comparable experiment is added.
4. Rerun the experiments with the actual Alibaba trace CSV before copying values into the manuscript.
5. Update every table and figure caption after rerunning because makespan and SLR definitions changed.
6. Insert ORCID for at least one author.
7. Submit the final `.docx` to professional or native English proofreading before upload.
