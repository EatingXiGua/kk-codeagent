from pathlib import Path


class Workspace:
    """Defines the filesystem boundary where the agent can operate."""

    DEFAULT_IGNORED_NAMES = {
        ".git",
        ".idea",
        ".vscode",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "node_modules",
        "target",
        "dist",
        "build",
        ".env",
        "secrets",
    }

    DEFAULT_IGNORED_PATTERNS = {
        ".env.*",
    }

    def __init__(
        self,
        root_path: str | Path,
        ignored_names: set[str] | None = None,
        ignored_patterns: set[str] | None = None,
    ):
        self.root = Path(root_path).resolve()
        self.ignored_names = (
            ignored_names
            if ignored_names is not None
            else set(self.DEFAULT_IGNORED_NAMES)
        )
        self.ignored_patterns = (
            ignored_patterns
            if ignored_patterns is not None
            else set(self.DEFAULT_IGNORED_PATTERNS)
        )

        if not self.root.exists():
            raise FileNotFoundError(f"Workspace does not exist: {self.root}")

        if not self.root.is_dir():
            raise NotADirectoryError(
                f"Workspace root is not a directory: {self.root}"
            )

    def resolve_path(self, relative_path: str | Path) -> Path:
        """Resolve a workspace-relative path and block path escape."""
        target_path = (self.root / relative_path).resolve()

        try:
            target_path.relative_to(self.root)
        except ValueError as exc:
            raise PermissionError(
                "Access outside the workspace is forbidden: "
                f"{relative_path}"
            ) from exc

        return target_path

    def resolve_file(self, relative_path: str | Path) -> Path:
        """Resolve a workspace-relative path that must be an existing file."""
        file_path = self.resolve_path(relative_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {relative_path}")

        if not file_path.is_file():
            raise IsADirectoryError(f"Path is not a file: {relative_path}")

        return file_path

    def resolve_dir(self, relative_path: str | Path) -> Path:
        """Resolve a workspace-relative path that must be an existing directory."""
        dir_path = self.resolve_path(relative_path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {relative_path}")

        if not dir_path.is_dir():
            raise NotADirectoryError(
                f"Path is not a directory: {relative_path}"
            )

        return dir_path

    def relative_path(self, path: str | Path) -> Path:
        """Return a path relative to the workspace root."""
        return self.resolve_path(path).relative_to(self.root)

    def should_ignore(self, path: str | Path) -> bool:
        """Return True when a path should be hidden from agent tools."""
        resolved_path = self.resolve_path(path)
        relative_path = resolved_path.relative_to(self.root)

        return any(
            part in self.ignored_names
            or any(Path(part).match(pattern) for pattern in self.ignored_patterns)
            for part in relative_path.parts
        )
