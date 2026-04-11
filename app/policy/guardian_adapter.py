from pathlib import PurePosixPath


class GuardianAdapter:
    def approve(self, *, files_changed: int, changed_paths: list[str], max_files: int, allowed_paths: list[str]) -> bool:
        if files_changed > max_files:
            return False

        if not allowed_paths:
            return True

        return all(self._is_allowed(path, allowed_paths) for path in changed_paths)

    @staticmethod
    def _is_allowed(path: str, allowed_paths: list[str]) -> bool:
        normalized = PurePosixPath(path)
        return any(normalized.match(pattern) for pattern in allowed_paths)
