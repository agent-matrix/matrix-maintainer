from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from matrix_maintainer.models import ExecutionResult
from matrix_maintainer.settings import get_settings


def _try_matrixlab(repo_dir: Path, command: list[str], timeout_seconds: int) -> ExecutionResult | None:
    settings = get_settings()
    if not settings.matrixlab_enabled:
        return None
    if shutil.which(settings.matrixlab_bin) is None:
        return None

    matrixlab_command = [settings.matrixlab_bin, "exec", "--cwd", str(repo_dir), "--"] + command
    start = time.time()
    proc = subprocess.run(
        matrixlab_command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    end = time.time()
    return ExecutionResult(
        command=" ".join(matrixlab_command),
        return_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        duration_seconds=round(end - start, 3),
    )


def execute_command(repo_dir: Path, command: list[str], timeout_seconds: int) -> ExecutionResult:
    settings = get_settings()
    matrixlab_result = _try_matrixlab(repo_dir, command, timeout_seconds)
    if matrixlab_result is not None:
        return matrixlab_result

    if not settings.matrixlab_fallback_local:
        return ExecutionResult(
            command=" ".join(command),
            return_code=127,
            stderr="matrixlab unavailable and local fallback disabled",
        )

    start = time.time()
    proc = subprocess.run(
        command,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        env={**os.environ},
    )
    end = time.time()
    return ExecutionResult(
        command=" ".join(command),
        return_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        duration_seconds=round(end - start, 3),
    )
