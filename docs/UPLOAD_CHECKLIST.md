# BIGAPI Upload Checklist

Use this checklist after the manuscript source file is available. The repository currently has only the PDF, so final journal formatting and Word upload must be completed from the editable manuscript source.

## 1. Prepare Local Environment

```bash
cd /Users/omyadav/Documents/ChatGPT/quant1/hub
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

Optional but recommended for exact paper reproduction:

```bash
python scripts/download_alibaba_batch_task.py
```

## 2. Verify Code

```bash
source .venv/bin/activate
pytest
python -m compileall evaluation simulation schedulers optimizers experiments
```

## 3. Regenerate Core Results

Run the full optimizer comparison after adding or downloading the Alibaba trace CSV:

```bash
source .venv/bin/activate
python experiments/hybrid_experiment.py
python evaluation/improvements.py
```

Expected outputs:

```text
results/csv/phase2_full_comparison.csv
results/csv/phase2_improvement_report.csv
results/csv/phase2_best_weights.csv
results/csv/final_summary_table.csv
results/plots/convergence_curves.png
results/plots/cce_subgroup_convergence.png
results/plots/scheduler_comparison.png
results/plots/slr_comparison.png
results/plots/weight_vectors_heatmap.png
results/plots/improvement_over_mect.png
results/plots/radar_profile.png
results/plots/runtime_vs_fitness.png
```

## 4. Run Reviewer-Requested Additional Analyses

Quick smoke run:

```bash
source .venv/bin/activate
python experiments/sensitivity_analysis.py --tasks 500 --pop-size 10 --iterations 10
python experiments/robustness_experiment.py --tasks 500
```

Paper-grade run:

```bash
source .venv/bin/activate
python experiments/sensitivity_analysis.py --tasks 1000 --pop-size 20 --iterations 50
python experiments/robustness_experiment.py --tasks 1000 --reoptimize-de --pop-size 20 --iterations 50
```

Expected outputs:

```text
results/csv/fitness_weight_sensitivity.csv
results/csv/robustness_scenarios.csv
```

## 5. Update Manuscript

1. Replace the abstract with the structured one-paragraph version from `docs/BIGAPI_REVIEW_REVISION_PLAN.md`, after inserting final numerical results.
2. Rewrite the introduction and related work using the 2025-2026 references listed in the revision plan.
3. Replace the fitness equation with the six-objective version.
4. Replace the SLR equation and explain the parallel lower bound.
5. Remove the direct SLR percentage comparison against Li and Chen unless a comparable experiment is added.
6. Update all tables using the newly generated CSV files.
7. Replace all low-resolution figures with regenerated plots from `results/plots`.
8. Cite every figure and chart in the main text before or near its first appearance.
9. Insert the notation table and define every symbol used in equations.
10. Add at least one author ORCID.
11. Renumber all references sequentially in the journal's required style.
12. Apply native/professional English proofreading to the final `.docx`.

## 6. Create Upload Package

Prepare these files for the publisher portal:

```text
Revised_Manuscript.docx
Response_to_Reviewers.docx
Highlights_or_Cover_Letter.docx, if required
Editable figure files, if required
High-resolution figure images
Supplementary CSV or code archive, if allowed
```

Before upload:

1. Confirm the manuscript title, author order, affiliations, and ORCID.
2. Confirm the abstract is one paragraph and approximately 200 words.
3. Confirm the conclusion is approximately 300-350 words.
4. Confirm each reviewer comment is answered in the response letter.
5. Confirm the manuscript and response letter use the same final result values.
6. Confirm there are no placeholder values such as `TBD`, `XX`, or bracketed instructions.

## 7. Portal Upload Steps

1. Log in to the journal submission portal.
2. Open the revision task for the manuscript.
3. Upload `Revised_Manuscript.docx` as the main article file.
4. Upload `Response_to_Reviewers.docx` as the response/rebuttal file.
5. Upload figures separately if the portal requests source image files.
6. Add ORCID in the author metadata page if it is not imported from the Word file.
7. Paste or upload the cover letter if required.
8. Review the generated PDF proof carefully.
9. Check equations, figure captions, table alignment, reference numbering, and author metadata.
10. Submit only after the portal PDF matches the Word file.
