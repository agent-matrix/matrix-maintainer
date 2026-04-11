class TreasuryAdapter:
    def authorize(self, *, estimated_cost_mxu: float, budget_remaining_mxu: float) -> bool:
        return estimated_cost_mxu <= budget_remaining_mxu
