from matrix_maintainer.models import RepoHealthReport

def summarize_health(report: RepoHealthReport) -> str:
    return f"{report.repo.full_name}: {report.status}"
