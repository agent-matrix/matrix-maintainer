def summarize_run(status: str, pr_url: str | None = None, cost_mxu: float | None = None) -> dict[str, str | float]:
    summary: dict[str, str | float] = {"status": status}
    if pr_url:
        summary["pr"] = pr_url
    if cost_mxu is not None:
        summary["cost"] = cost_mxu
    return summary
