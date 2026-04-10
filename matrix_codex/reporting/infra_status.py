from matrix_codex.models import InfraStatus

def default_infra_status() -> list[InfraStatus]:
    return [
        InfraStatus(name="GitHub API", status="unknown", details="Checked indirectly through discovery."),
        InfraStatus(name="GitPilot", status="unknown", details="Adapter availability is checked during runs."),
        InfraStatus(name="matrixlab", status="unknown", details="Adapter availability is checked during runs."),
    ]
