from typing import ClassVar

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from workspace.workspace import Workspace


class ListFilesInput(BaseModel):
    path: str = Field(
        default=".",
        description="Directory path relative to the workspace root.",
    )
    recursive: bool = Field(
        default=False,
        description="Whether to list files recursively.",
    )
    max_results: int = Field(
        default=200,
        gt=0,
        description="Maximum number of entries to return.",
    )


class ListFilesTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "list_files"
    description: str = "List files and directories in the workspace."
    args_schema: type[BaseModel] = ListFilesInput

    workspace: Workspace

    ignored_names: ClassVar[set[str]] = {
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
    }

    def _run(
        self,
        path: str = ".",
        recursive: bool = False,
        max_results: int = 200,
    ) -> str:
        target_path = self.workspace.resolve_path(path)

        if not target_path.exists():
            return f"Path does not exist: {path}"

        if not target_path.is_dir():
            return f"Path is not a directory: {path}"

        iterator = (
            target_path.rglob("*")
            if recursive
            else target_path.iterdir()
        )
        results: list[str] = []

        try:
            for item in iterator:
                if any(part in self.ignored_names for part in item.parts):
                    continue

                relative_path = item.relative_to(self.workspace.root)

                if item.is_symlink():
                    item_type = "[LINK]"
                elif item.is_dir():
                    item_type = "[DIR]"
                elif item.is_file():
                    item_type = "[FILE]"
                else:
                    item_type = "[OTHER]"

                results.append(f"{item_type} {relative_path}")

                if len(results) >= max_results:
                    results.append(
                        f"Result count exceeded {max_results}; truncated."
                    )
                    break
        except PermissionError as exc:
            return f"Permission denied while reading directory: {exc}"
        except OSError as exc:
            return f"Failed to read directory: {exc}"

        if not results:
            return f"Directory is empty: {path}"

        return "\n".join(results)
