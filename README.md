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
| Schedule Length Ratio (SLR) | Scheduling efficiency |

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
pip install -r requirements.txt
```

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
