from dataclasses import dataclass


@dataclass
class CostTracker:
    total_cost: float = 0.0

    def add_cost(self, amount: float) -> None:
        self.total_cost += amount

    def reset(self):
        self.total_cost = 0.0
