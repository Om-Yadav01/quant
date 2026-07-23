import numpy as np


class LeastLoadedScheduler:
    name = "Least Loaded"

    def select(self, nodes: list, workload_size: float) -> int:
        return int(np.argmin([nd["queue_workload"] for nd in nodes]))

    def reset(self) -> None:
        pass


