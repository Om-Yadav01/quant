# Response To Reviewers Draft

Dear Editor and Reviewers,

We thank the reviewers for their careful reading and constructive comments. We have revised the manuscript, experiments, and accompanying code to address the methodological and presentation concerns. The major changes include a revised six-objective fitness function, constrained nonnegative scheduling weights, a corrected Schedule Length Ratio definition, consistent MECT normalization constants, real Alibaba trace reruns, coefficient sensitivity analysis, robustness experiments across multiple workload settings, expanded result interpretation, and updated manuscript text for the abstract, conclusion, notation, and related work.

## Reviewer #1

**Comment 1. The authors should ask the help of native English-speaking proofreader, because there are some typo and linguistic mistakes that should be fixed.**

Response: We agree. The revised manuscript should be proofread by a native English-speaking colleague or professional editing service before upload. We have also rewritten the abstract and conclusion drafts to improve clarity and technical precision.

**Comment 2. Abstract to modify: the abstract should contain Objectives, Methods/Analysis, Findings, and Novelty/Improvement. It is suggested to present the abstract in one 200 words paragraph.**

Response: We revised the abstract as a single structured paragraph of approximately 190 words, explicitly covering Objectives, Methods/Analysis, Findings, and Novelty/Improvement.

**Comment 3. The introduction is poorly written, and it does not properly refer to previously published studies.**

Response: We will revise the introduction to better explain the literature gap: many prior schedulers optimize static or narrowly defined objectives, while fewer evaluate dynamic heterogeneous scheduling under trace-derived arrivals with sensitivity and robustness testing. We added recent 2025-2026 references to support this discussion.

**Comment 4. It is important to add some recent work (2025-2026) to the literature review. At least 5 new references should be added to the article.**

Response: We added six recent references from 2025-2026 covering metaheuristic edge scheduling, reinforcement-learning task scheduling, SLA-aware scheduling, and hybrid deep-learning scheduling.

**Comment 5. The quality of the figures is not acceptable.**

Response: Figures should be regenerated from `results/plots` after the final experiment run and exported at high resolution. The result-generation scripts now regenerate all comparison, convergence, weight, improvement, and radar plots.

**Comment 6. Much more explanations and interpretations should be added for the result.**

Response: We expanded the result interpretation to focus on multi-metric trade-offs. In the real Alibaba trace run, optimized policies improve AvgCT by 14.59-21.27% and P95 by 4.06-13.79% relative to MECT in the main 1,000-task setting, but not all metrics improve under all robustness scenarios. We will report these trade-offs explicitly.

**Comment 7. It is suggested to compare the results of the present study with previous studies and analyze their results completely.**

Response: We revised the comparison with prior work to be qualitative where metric definitions differ. We removed the invalid claim that our SLR improvement directly exceeds Li and Chen's benchmark, because their SLR formulation is not directly comparable to ours.

**Comment 8. The conclusion section needs to be rewritten.**

Response: We prepared a revised conclusion of approximately 301 words. It summarizes the corrected objective, main findings, limitations, robustness results, and future work.

**Comment 9. All charts and figures must be clearly cited and referenced within the main text.**

Response: We will cite each figure in the main text before or near its first appearance and add explanatory text after each figure.

**Comment 10. All symbols and parameters should be defined.**

Response: We prepared a notation table defining all policy weights, queue variables, speed, latency, failure probability, completion time, P95, makespan, SLR, arrival window, and workload scale.

**Comment 11. The reference list should be formatted according to the journal's guidelines.**

Response: We will renumber all references sequentially in the journal style and update in-text citations to the required `[1]`, `[2]` format.

**Comment 12. The manuscript does not follow the format requested by the Journal.**

Response: We will prepare the final article in the required Word template, include ORCID, verify captions/tables/references, and upload the Word version as requested by the technical editor.

## Reviewer #3

**Comment 1. The manuscript describes six competing objectives, whereas Equation (7) optimizes only four quantities.**

Response: We agree and revised the fitness function to include all six stated objectives. The implemented normalized objective is:

```text
F = 0.25 r_avgCT + 0.20 r_P95 + 0.20 r_makespan
    + 0.10 r_load_variance + 0.15 r_failure_rate + 0.10 r_SLR
```

P95 latency and SLR are no longer only post-hoc metrics; they directly contribute to the optimization objective.

**Comment 2. The rationale for the coefficients in Equation (7) is insufficient.**

Response: We corrected the coefficient inconsistency and added `experiments/sensitivity_analysis.py`. The sensitivity run evaluates balanced, mean-latency-heavy, tail-latency-heavy, makespan/SLR-heavy, reliability-heavy, and fairness-heavy profiles. The balanced profile is retained because it avoids the strongest single-metric regressions.

**Comment 3. The MECT normalization values in Section 4 differ from Tables 4 and 5.**

Response: We corrected the workflow so MECT metrics are generated once through `set_baselines_from_metrics()` and reused consistently by the fitness function and result tables. The main run uses a real Alibaba trace sample with 14,058,462 valid cleaned records.

**Comment 4. The proposed SLR definition in Equation (8) requires reconsideration.**

Response: We agree. We replaced the previous denominator with a parallel lower bound derived from aggregate cluster capacity, task release times, and fastest feasible task durations. The revised SLR is therefore:

```text
SLR = observed makespan / parallel lower bound
```

**Comment 5. The comparison with Li and Chen [18] is not methodologically valid.**

Response: We agree and removed the direct numerical comparison. We now compare against prior work qualitatively unless the benchmark setting and SLR definition are directly aligned.

**Comment 6. Allowing weights to range from -5 to 5 can reverse penalty features.**

Response: We changed the search range to `[0, 5]`. Because the scheduler formula already subtracts queue, latency, failure probability, and execution cost terms, nonnegative weights preserve the intended penalty semantics.

**Comment 7. Sampling only 1,000 records and compressing arrivals into a 600-second window may alter workload dynamics.**

Response: We added and ran `experiments/robustness_experiment.py` with repeated samples, 300/600/1200-second arrival windows, light/heavy workload scales, and 10/15/25-node clusters. The results show that improvements are not uniform under all settings, so we revised the manuscript claims to present the method as promising and adaptive rather than universally dominant.

## Technical Editor

**Please upload the Word version of the article.**

Response: The final upload package must include `Revised_Manuscript.docx`. The editable manuscript source is still needed to create the journal-formatted Word file.

**Please add an ORCID for at least one author.**

Response: We will add at least one author ORCID in the title page and submission metadata.

**Please address English revisions.**

Response: We will complete professional/native English proofreading before final upload.
