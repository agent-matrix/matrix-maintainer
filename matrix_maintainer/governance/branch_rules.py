from datetime import datetime, timezone

from matrix_maintainer.constants import STANDARD_BRANCH_PREFIX

def build_branch_name(repo_name: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{STANDARD_BRANCH_PREFIX}-{repo_name}-{stamp}"
