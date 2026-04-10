"""Backward-compatible import shim.

matrix-codex is the new package name; matrix_maintainer remains as a thin alias.
"""

from matrix_codex import *  # noqa: F401,F403
