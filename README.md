# Dynamic Resource Scheduling using Hybrid Evolutionary Optimization

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Research%20Project-success?style=for-the-badge)

</p>

<p align="center">
<strong>A simulation framework for evaluating dynamic resource scheduling strategies in heterogeneous distributed computing environments using classical scheduling algorithms and evolutionary optimization techniques.</strong>
</p>

---

## 📖 Overview

Dynamic Resource Scheduling is a simulation framework designed to evaluate scheduling strategies in heterogeneous distributed computing environments.

The framework models a cluster of compute nodes with varying processing capabilities, queue workloads, communication latency, execution cost, available capacity, and probabilistic failures. Incoming computational tasks are dynamically assigned to resources using multiple scheduling strategies.

Unlike traditional heuristic schedulers, this project introduces a **policy-based scheduler** whose decision weights are optimized using evolutionary optimization algorithms, enabling adaptive scheduling under changing system conditions.

---

## 🎯 Objectives

- Simulate dynamic resource allocation in heterogeneous computing clusters.
- Compare traditional scheduling algorithms with optimization-driven approaches.
- Optimize scheduling policy weights using evolutionary algorithms.
- Evaluate scheduling quality using multiple performance metrics.
- Visualize and compare scheduler performance under identical workloads.

---

# ✨ Features

- Dynamic task scheduling simulation
- Heterogeneous compute node modeling
- Synthetic workload generation
- Policy-based scheduling
- Failure-aware scheduling with retry mechanism
- Evolutionary optimization of scheduling policies
- Automated benchmarking
- Statistical performance evaluation
- CSV result generation
- Performance visualization

---

# 🏗️ System Architecture

```text
                   Incoming Tasks
                         │
                         ▼
                Workload Generator
                         │
                         ▼
             Scheduling Algorithms
      ┌─────────────┬──────────────┬──────────────┐
      │             │              │
 Round Robin   Least Loaded      MECT
      │             │              │
      └─────────────┴──────────────┘
                         │
                         ▼
                 Policy Scheduler
                         │
                         ▼
         Evolutionary Optimization Layer
      ┌──────────┬──────────┬──────────┐
      │    GA    │   PSO    │    DE    │
      └──────────┴──────────┴──────────┘
                         │
                         ▼
              Hybrid CCE Optimizer
                         │
                         ▼
             Cluster Simulation Engine
                         │
                         ▼
          Evaluation & Visualization
```

---

# ⚙️ Scheduling Algorithms

## Round Robin

Assigns incoming tasks sequentially across all available compute nodes without considering resource state.

### Advantages

- Simple implementation
- Minimal scheduling overhead

### Limitation

- Ignores workload imbalance and resource heterogeneity

---

## Least Loaded

Selects the compute node currently handling the lowest workload, improving load balancing compared to Round Robin.

---

## Minimum Estimated Completion Time (MECT)

Schedules tasks to the compute node expected to complete execution earliest by considering estimated execution time.

---

## Policy Scheduler

The Policy Scheduler computes a weighted score for every compute node using normalized resource characteristics.

Scheduling decisions consider:

| Parameter | Description |
|------------|-------------|
| Processing Speed | Faster task execution |
| Queue Workload | Current congestion level |
| Network Latency | Communication delay |
| Failure Probability | Node reliability |
| Available Capacity | Remaining computational resources |
| Execution Cost | Resource usage cost |

The compute node with the highest score is selected.

---

# 🧬 Evolutionary Optimization

Scheduling policy weights are optimized using the following algorithms.

## Genetic Algorithm (GA)

Population-based optimization using:

- Selection
- Crossover
- Mutation

---

## Particle Swarm Optimization (PSO)

Population intelligence inspired by collective swarm behaviour.

---

## Differential Evolution (DE)

Continuous optimization through mutation and recombination of candidate solutions.

---

## Hybrid CCE Optimizer

A hybrid optimization strategy combining complementary search behaviours to improve convergence while avoiding local optima during policy weight optimization.

---

# 🔄 Simulation Workflow

```text
Generate Workload
        │
        ▼
Create Cluster
        │
        ▼
Select Scheduler
        │
        ▼
Dispatch Tasks
        │
        ▼
Execute Simulation
        │
        ▼
Failure Handling
        │
        ▼
Collect Metrics
        │
        ▼
Optimization
        │
        ▼
Visualization
```

---

# 📂 Project Structure

```text
Dynamic-Resource-Scheduling
│
├── data/                 # Resource metadata
├── evaluation/           # Performance metrics and analysis
├── experiments/          # Experimental workflows
├── optimizers/           # GA, PSO, DE and Hybrid CCE Optimizer
├── schedulers/           # Scheduling algorithms
├── simulation/           # Cluster and task simulation
├── visualization/        # Performance visualization
├── requirements.txt
└── README.md
```

---

# 📊 Performance Metrics

The framework evaluates scheduler performance using:

| Metric | Description |
|---------|-------------|
| Average Completion Time | Mean task completion time |
| P95 Latency | 95th percentile task latency |
| Throughput | Tasks completed per unit time |
| Makespan | Total execution time |
| Load Variance | Degree of workload balancing |
| Failure Rate | Fraction of failed executions |
| Schedule Length Ratio (SLR) | Makespan divided by an internal parallel lower bound |
| SLR Lower Bound | Parallel lower bound used for SLR normalization |

---

# Publisher Revision Workflow

This branch includes changes prepared for the BIGAPI publisher review response.

Key reviewer-driven updates:

- Fitness now optimizes all six stated objectives: average completion time, P95 latency, makespan, load variance, failure rate, and SLR.
- Policy weights are constrained to `[0, 5]` so queue, latency, failure, and execution-cost terms cannot become accidental rewards.
- Makespan is measured from first task arrival to last task finish.
- SLR is normalized by a parallel lower bound instead of the previous serial sum of fastest task times.
- MECT normalization constants are generated from one baseline metrics object and reused by the experiments.
- Sensitivity and robustness scripts were added for reviewer-requested validation.

Revision documents:

```text
docs/BIGAPI_REVIEW_REVISION_PLAN.md
docs/UPLOAD_CHECKLIST.md
docs/REAL_DATA_RESULTS_SUMMARY.md
docs/RESPONSE_TO_REVIEWERS_DRAFT.md
```

## Submission Ready Package

The final revision package is generated in:

```text
submission_ready/
```

It contains:

```text
Revised_Manuscript.docx
Response_to_Reviewers.docx
Cover_Letter.docx
Author_Metadata_and_Upload_Checklist.docx
SUBMISSION_PACKAGE_MANIFEST.txt
BIGAPI_Submission_Package.zip
figures/
csv/
```

To rebuild the package after rerunning experiments:

```bash
source .venv/bin/activate
python scripts/build_submission_package.py
```

Upload sequence for the journal portal:

1. Upload `submission_ready/Revised_Manuscript.docx` as the main article file.
2. Upload `submission_ready/Response_to_Reviewers.docx` as the reviewer response.
3. Upload `submission_ready/Cover_Letter.docx` if the portal asks for a cover letter.
4. Upload the referenced high-resolution figures from `submission_ready/figures/` if requested separately.
5. Enter at least one verified author ORCID in the portal before final submission.
6. Review the portal-generated PDF proof before pressing submit.

Author-only item still required: add a verified ORCID for at least one author. The repository does not invent ORCID identifiers.

---

# 📈 Experimental Pipeline

```text
Schedulers
      │
      ▼
Simulation
      │
      ▼
Evaluation
      │
      ▼
Optimization
      │
      ▼
CSV Results
      │
      ▼
Performance Graphs
```

---

# 🛠️ Technologies Used

| Category | Technology |
|-----------|------------|
| Programming Language | Python |
| Numerical Computing | NumPy |
| Data Processing | Pandas |
| Visualization | Matplotlib |

---

# 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/Divyanshukash/Dynamic-Scheduling-.git
```

Navigate into the project directory:

```bash
cd Dynamic-Scheduling-
```

Install the required dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

For exact manuscript reproduction, place the Alibaba Cluster Trace file here:

```text
data/alibaba_trace/batch_task.csv
```

If you do not already have the file, download and verify the official Alibaba `batch_task.tar.gz` archive:

```bash
python scripts/download_alibaba_batch_task.py
```

If this file is absent, the code falls back to synthetic workload generation.

---

# ▶️ Running Experiments

Run baseline scheduling experiments:

```bash
python experiments/run_baselines.py
```

Run optimizer-based experiments:

```bash
python experiments/optimizer_experiment.py
```

Run the hybrid optimization experiment:

```bash
python experiments/hybrid_experiment.py
```

Run coefficient sensitivity analysis:

```bash
python experiments/sensitivity_analysis.py --tasks 1000 --pop-size 20 --iterations 50
```

Run robustness checks across samples, arrival windows, workload intensity, and cluster size:

```bash
python experiments/robustness_experiment.py --tasks 1000 --reoptimize-de --pop-size 20 --iterations 50
```

Run tests:

```bash
pytest
python -m compileall evaluation simulation schedulers optimizers experiments
```

---

# 📁 Output

The framework generates:

- Scheduler comparison results
- Optimized policy weights
- Performance metrics
- CSV reports
- Comparative plots
- Experimental summaries

---

# 📌 Future Enhancements

- Reinforcement Learning–based scheduler
- Kubernetes integration
- Energy-aware scheduling
- GPU resource scheduling
- Multi-objective optimization
- Real-world cloud workload traces
- Interactive performance dashboard

---

# 🤝 Contributing

Contributions are welcome. Improvements to scheduling algorithms, optimization techniques, evaluation metrics, and visualization modules are encouraged.

---

# 📄 License

This project was developed for academic and research purposes.
