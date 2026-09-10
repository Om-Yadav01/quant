# Real Alibaba Trace Results Summary

These results were generated with the official Alibaba Cluster Trace 2018 `batch_task.tar.gz` file. The archive was downloaded from Alibaba's public trace URL and verified with SHA256:

```text
7c4b32361bd1ec2083647a8f52a6854a03bc125ca5c202652316c499fbf978c6  batch_task.tar.gz
```

Dataset extraction and sampling log:

```text
Raw rows loaded    : 14,295,731
Terminated tasks   : 14,059,143
Rows after cleaning: 14,058,462
Tasks sampled      : 1,000
Arrival window     : 0.0s to 600.0s
Workload range     : 10.0 to 84.4 units
Workload mean      : 54.72 units
```

## Main 1,000-Task Result

| Scheduler | AvgCT | P95 | Makespan | SLR | LoadVar | FailRate | Throughput |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Round Robin | 82.6471 | 464.3882 | 1274.7433 | 2.1075 | 3.8222 | 0.024 | 0.7845 |
| Least Loaded | 9.6450 | 21.5953 | 633.4151 | 1.0472 | 838.0889 | 0.014 | 1.5787 |
| MECT | 12.0373 | 18.7934 | 619.6140 | 1.0244 | 1273.0222 | 0.014 | 1.6139 |
| GA | 9.8497 | 16.6843 | 620.1830 | 1.0253 | 1391.6889 | 0.010 | 1.6124 |
| PSO | 9.4771 | 18.0310 | 619.1322 | 1.0236 | 1272.6222 | 0.010 | 1.6152 |
| DE | 10.1367 | 16.2014 | 617.5510 | 1.0210 | 1490.6222 | 0.011 | 1.6193 |
| Hybrid CCE | 10.2805 | 16.5822 | 621.3535 | 1.0273 | 1428.4889 | 0.017 | 1.6094 |

## Improvement Over MECT

| Optimizer | AvgCT | P95 | Makespan | SLR | LoadVar | FailRate | Throughput |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GA | +18.17% | +11.22% | -0.09% | -0.09% | -9.32% | +28.57% | -0.09% |
| PSO | +21.27% | +4.06% | +0.08% | +0.08% | +0.03% | +28.57% | +0.08% |
| DE | +15.79% | +13.79% | +0.33% | +0.33% | -17.09% | +21.43% | +0.33% |
| Hybrid CCE | +14.59% | +11.77% | -0.28% | -0.28% | -12.21% | -21.43% | -0.28% |

Positive percentages mean better performance than MECT. Negative percentages identify a regression and must be reported transparently.

## Fitness Weight Sensitivity

| Profile | AvgCT | P95 | Makespan | SLR | LoadVar | FailRate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Balanced six-objective | 10.0599 | 16.6096 | 621.9211 | 1.0282 | 1420.6222 | 0.012 |
| Mean latency heavy | 9.8894 | 17.1334 | 621.0170 | 1.0267 | 1391.2889 | 0.015 |
| Tail latency heavy | 10.0381 | 16.6843 | 621.5958 | 1.0277 | 1418.6222 | 0.009 |
| Makespan/SLR heavy | 9.9685 | 16.1125 | 621.1170 | 1.0269 | 1373.4222 | 0.013 |
| Reliability heavy | 10.5916 | 16.8022 | 621.2942 | 1.0272 | 1492.0889 | 0.015 |
| Fairness heavy | 9.4130 | 21.2710 | 627.6816 | 1.0377 | 984.3556 | 0.017 |

Interpretation: the balanced coefficient set is defensible because it avoids the strongest single-metric trade-offs. The fairness-heavy setting lowers load variance but worsens P95, makespan, SLR, and failure rate. Tail/makespan profiles improve specific objectives but do not dominate the balanced setting.

## Robustness Summary

`experiments/robustness_experiment.py` tested nine scenarios: three samples, three arrival windows, light/heavy workload intensity, and 10/25-node clusters. The reoptimized DE policy improved AvgCT by an average of +6.66%, P95 by +1.83%, and failure rate by +12.07% against MECT, but it regressed on makespan/SLR by an average of -2.16%.

The robustness table should be presented as nuanced evidence, not as universal dominance. In particular:

- The policy improves the baseline 600-second trace sample on AvgCT, P95, makespan, SLR, and failure rate.
- Performance is sensitive to arrival-window compression; the 300-second compressed window regresses on AvgCT, P95, makespan, and SLR.
- Performance is sensitive to cluster size; the 10-node small-cluster case regresses on AvgCT, P95, makespan, and SLR.
- The conclusion should state that the method is promising under the main real-trace setting, but future work should improve robustness under heavier contention and different cluster scales.

## Publishable Claim Wording

Use this style:

> On the main 1,000-task Alibaba trace sample, the optimized policies reduce average completion time by 14.59-21.27% and P95 latency by 4.06-13.79% relative to MECT. DE provides the best P95, makespan, SLR, and throughput, while PSO provides the best average completion time and failure rate. Robustness tests show that these improvements are not uniform across all arrival windows and cluster sizes, so the method should be interpreted as a promising adaptive scheduler rather than a universally dominant scheduler.

Avoid these claims:

- "CCE has no regression on any dimension."
- "SLR improves by 95% and exceeds Li and Chen."
- "The method is robust in all workload settings."
- "All optimizers outperform MECT on every metric."
