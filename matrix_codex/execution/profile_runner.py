from __future__ import annotations

import subprocess
from pathlib import Path

import yaml


def load_profiles(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run_commands(commands: list[str], cwd: Path) -> None:
    for command in commands:
        proc = subprocess.run(command, shell=True, cwd=cwd, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"command_failed={command}")


def run_profile(profile_name: str, repo_dir: Path, profiles_path: Path) -> None:
    data = load_profiles(profiles_path)
    profile = data.get("profiles", {}).get(profile_name)
    if not profile:
        raise RuntimeError(f"unknown_profile={profile_name}")
    run_commands(profile.get("install", []), repo_dir)
    run_commands(profile.get("validate", []), repo_dir)
