"""Path traversal validation and filesystem sandbox enforcement."""

import os
from pathlib import Path
from typing import Union
from proton.core.exceptions import SecurityError


class FilesystemSandbox:
    """Enforces that file operations remain strictly within allowed root paths."""

    def __init__(self, workspace_root: Union[str, Path]) -> None:
        self.workspace_root = Path(workspace_root).resolve()

    def validate_path(self, path: Union[str, Path], allow_read_outside: bool = False) -> Path:
        """Validate and resolve path. Raises SecurityError on path traversal outside workspace."""
        try:
            expanded = os.path.expanduser(str(path))
            target = Path(expanded)
            if not target.is_absolute():
                resolved = (self.workspace_root / target).resolve()
            else:
                resolved = target.resolve()

            # Check if resolved path is inside workspace_root
            if not allow_read_outside:
                try:
                    resolved.relative_to(self.workspace_root)
                except ValueError:
                    raise SecurityError(
                        f"Filesystem access outside workspace boundary is blocked: {path} (Resolved: {resolved})"
                    )

            return resolved
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Invalid path traversal attempt: {path}") from e

    def is_safe_relpath(self, path: Union[str, Path]) -> bool:
        """Check if path is safely inside workspace without throwing."""
        try:
            self.validate_path(path)
            return True
        except SecurityError:
            return False
