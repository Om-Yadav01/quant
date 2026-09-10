import numpy as np
import pandas as pd
import os

_PROJECT_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATASET_PATH = os.path.join(_PROJECT_ROOT, "data", "alibaba_trace", "batch_task.csv")

def load_tasks_from_dataset(
    num_tasks:      int = 1000,
    dataset_path:   str = DEFAULT_DATASET_PATH,
    rng:            np.random.Generator = None,
    arrival_window: float = 600.0,
    workload_scale: float = 1.0,
) -> pd.DataFrame:
    if rng is None:
        rng = np.random.default_rng(42)
 
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"\n[ERROR] Dataset not found at: {dataset_path}\n"
            f"  Place batch_task.csv inside: {os.path.dirname(dataset_path)}/"
        )
 
    print(f"[dataset] Loading batch_task.csv from '{dataset_path}' ...")
 
    COL_NAMES = [
        "task_name", "instance_num", "job_name", "task_type", "status",
        "start_time", "end_time", "plan_cpu", "plan_mem",
    ]
    df_raw = pd.read_csv(
        dataset_path,
        header=None,
        names=COL_NAMES,
        usecols=["task_name", "start_time", "plan_cpu", "status"],
        low_memory=False,
    )
    print(f"[dataset] Raw rows loaded    : {len(df_raw):,}")
 
    df_raw["status"] = df_raw["status"].astype(str).str.strip()
    df_clean = df_raw[df_raw["status"] == "Terminated"].copy()
    print(f"[dataset] Terminated tasks   : {len(df_clean):,}")
 
    df_clean = df_clean.dropna(subset=["start_time", "plan_cpu"])
 
    df_clean["plan_cpu"]    = pd.to_numeric(df_clean["plan_cpu"],    errors="coerce")
    df_clean["start_time"]  = pd.to_numeric(df_clean["start_time"],  errors="coerce")
    df_clean = df_clean.dropna(subset=["start_time", "plan_cpu"])
    df_clean = df_clean[df_clean["plan_cpu"] > 0]
    df_clean = df_clean[df_clean["start_time"] >= 0]
    print(f"[dataset] Rows after cleaning: {len(df_clean):,}")
 
    if len(df_clean) < num_tasks:
        raise ValueError(
            f"[ERROR] Only {len(df_clean):,} valid rows after cleaning, "
            f"but num_tasks={num_tasks} requested."
        )
 
    df_sample = df_clean.sample(
        n=num_tasks,
        random_state=int(rng.integers(1_000_000)),
        ignore_index=True,
    )
 
    print(f"[dataset] plan_cpu sample stats:")
    print(f"          min={df_sample['plan_cpu'].min():.1f}  "
          f"mean={df_sample['plan_cpu'].mean():.1f}  "
          f"max={df_sample['plan_cpu'].max():.1f}")
 
    raw_times  = df_sample["start_time"].values.astype(float)
    t_min      = raw_times.min()
    t_span     = raw_times.max() - t_min
    if t_span > 0:
        arrival_times = (raw_times - t_min) / t_span * arrival_window
    else:
        arrival_times = raw_times - t_min
    arrival_times = pd.Series(arrival_times)
 
    cpu_vals  = df_sample["plan_cpu"].clip(lower=5.0, upper=1000.0)
    log_cpu   = np.log(cpu_vals)
    log_min   = np.log(5.0)
    log_max   = np.log(1000.0)
    workload_size = (10.0 + 90.0 * (log_cpu - log_min) / (log_max - log_min))
    workload_size = workload_size * workload_scale
    workload_size = workload_size.clip(10.0, 100.0).round(2)
 
    result = pd.DataFrame({
        "task_id"      : range(num_tasks),
        "arrival_time" : arrival_times.round(3).values,
        "workload_size": workload_size.values,
    })
 
    result = result.sort_values("arrival_time").reset_index(drop=True)
    result["task_id"] = range(num_tasks)
 
    print(f"[dataset] Tasks sampled      : {len(result):,}")
    print(f"[dataset] Arrival window     : "
          f"{result['arrival_time'].min():.1f}s "
          f"→ {result['arrival_time'].max():.1f}s")
    print(f"[dataset] Workload range     : "
          f"{result['workload_size'].min():.1f} "
          f"– {result['workload_size'].max():.1f} units")
    print(f"[dataset] Workload mean      : "
          f"{result['workload_size'].mean():.2f} units")
 
    return result


def generate_workload(n_tasks: int = 1000, rng: np.random.Generator = None) -> pd.DataFrame:
    return generate_synthetic_workload(n_tasks=n_tasks, rng=rng)


def generate_synthetic_workload(
    n_tasks: int = 1000,
    rng: np.random.Generator = None,
    arrival_window: float = 600.0,
    workload_scale: float = 1.0,
) -> pd.DataFrame:
    if rng is None:
        rng = np.random.default_rng(42)
 
    print(f"[dataset] Generating {n_tasks} synthetic tasks ...")
 
    inter_arrivals = rng.exponential(scale=2.5, size=n_tasks)
    arrival_times  = np.cumsum(inter_arrivals)
    raw_span = arrival_times.max() - arrival_times.min()
    if raw_span > 0:
        arrival_times = (arrival_times - arrival_times.min()) / raw_span * arrival_window
    else:
        arrival_times = arrival_times - arrival_times.min()
 
    raw_sizes   = rng.lognormal(mean=3.5, sigma=0.6, size=n_tasks)
    workload_sz = np.clip(raw_sizes * workload_scale, 10, 100).round(2)
 
    df = pd.DataFrame({
        "task_id"      : np.arange(n_tasks),
        "arrival_time" : arrival_times.round(3),
        "workload_size": workload_sz,
    })
 
    print(f"[dataset] Tasks generated    : {len(df):,}")
    print(f"[dataset] Arrival window     : "
          f"{df['arrival_time'].min():.1f}s → {df['arrival_time'].max():.1f}s")
    print(f"[dataset] Workload range     : "
          f"{df['workload_size'].min():.1f} – {df['workload_size'].max():.1f} units")
 
    return df

def get_workload(
    num_tasks:      int = 1000,
    dataset_path:   str = DEFAULT_DATASET_PATH,
    rng:            np.random.Generator = None,
    arrival_window: float = 600.0,
    workload_scale: float = 1.0,
) -> pd.DataFrame:
    if os.path.exists(dataset_path):
        return load_tasks_from_dataset(
            num_tasks, dataset_path, rng, arrival_window, workload_scale
        )
    else:
        print(f"[dataset] batch_task.csv not found at '{dataset_path}'.")
        print(f"[dataset] Falling back to synthetic workload generation.")
        return generate_synthetic_workload(
            num_tasks, rng, arrival_window, workload_scale
        )

