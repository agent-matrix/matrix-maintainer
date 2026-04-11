def build_plan(repo: str, issue: str) -> dict[str, object]:
    return {
        "repo": repo,
        "issue": issue,
        "plan": [
            "analyze failure",
            "apply targeted fix",
            "run validation",
        ],
    }
