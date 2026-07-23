class RoundRobinScheduler:
    name = "Round Robin"

    def __init__(self):
        self._counter = 0

    def select(self, nodes: list, workload_size: float) -> int:
        idx = self._counter % len(nodes)
        self._counter += 1
        return idx

    def reset(self) -> None:
        self._counter = 0


