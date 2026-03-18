from matrix_maintainer.models import RepoHealthReport

def classify_failure(report: RepoHealthReport) -> str:
    if not report.install_ok:
        return "install_failure"
    if not report.test_ok:
        return "test_failure"
    if not report.start_ok:
        return "start_failure"
    return "unknown"
