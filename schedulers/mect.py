import numpy as np

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulation.node_environment import estimate_completion_time


class MECTScheduler:
    name = "MECT"

    def select(self, nodes: list, workload_size: float) -> int:
        ects = [estimate_completion_time(nd, workload_size) for nd in nodes]
        return int(np.argmin(ects))

    def reset(self) -> None:
        pass

