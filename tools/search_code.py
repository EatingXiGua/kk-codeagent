import fnmatch
from typing import ClassVar

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from workspace.workspace import Workspace


class SearchCodeInput(BaseModel):
    query: str = Field(
        min_length=1,
        description="Keyword to search for.",
    )
    path: str = Field(
        default=".",
        description="Directory path relative to the workspace root.",
    )
    file_pattern: str | None = Field(
        default=None,
        description="Optional file name pattern, such as *.py.",
    )
    case_sensitive: bool = Field(
        default=False,
        description="Whether matching is case-sensitive.",
    )
    max_results: int = Field(
        default=100,
        gt=0,
        description="Maximum number of matching lines to return.",
    )


class SearchCodeTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "search_code"
    description: str = "Search text files in the workspace for a keyword."
    args_schema: type[BaseModel] = SearchCodeInput

    workspace: Workspace

    default_file_patterns: ClassVar[list[str]] = [
        "*.py",
        "*.java",
        "*.kt",
        "*.kts",
        "*.js",
        "*.jsx",
        "*.ts",
        "*.tsx",
        "*.vue",
        "*.html",
        "*.css",
        "*.scss",
        "*.xml",
        "*.yml",
        "*.yaml",
        "*.json",
        "*.toml",
        "*.properties",
        "*.sql",
        "*.md",
        "*.txt",
        "*.sh",
        "*.bat",
        "*.ps1",
    ]

    def _run(
        self,
        query: str,
        path: str = ".",
        file_pattern: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
    ) -> str:
        try:
            search_root = self.workspace.resolve_dir(path)
        except FileNotFoundError:
            return f"Search path does not exist: {path}"
        except NotADirectoryError:
            return f"Search path is not a directory: {path}"
        except PermissionError as exc:
            return str(exc)

        patterns = (
            [file_pattern]
            if file_pattern
            else self.default_file_patterns
        )
        target_query = query if case_sensitive else query.lower()
        results: list[str] = []
        searched_file_count = 0
        skipped_file_count = 0

        try:
            for file_path in search_root.rglob("*"):
                if not file_path.is_file() or file_path.is_symlink():
                    continue

                if self.workspace.should_ignore(file_path):
                    continue

                if not any(
                    fnmatch.fnmatch(file_path.name, pattern)
                    for pattern in patterns
                ):
                    continue

                searched_file_count += 1

                try:
                    content = file_path.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                except (PermissionError, OSError):
                    skipped_file_count += 1
                    continue

                for line_number, line in enumerate(
                    content.splitlines(),
                    start=1,
                ):
                    compared_line = line if case_sensitive else line.lower()

                    if target_query not in compared_line:
                        continue

                    relative_path = file_path.relative_to(self.workspace.root)
                    stripped_line = line.strip()

                    if len(stripped_line) > 300:
                        stripped_line = stripped_line[:300] + "..."

                    results.append(
                        f"{relative_path}:{line_number}: {stripped_line}"
                    )

                    if len(results) >= max_results:
                        break

                if len(results) >= max_results:
                    break

        except PermissionError as exc:
            return f"Permission denied while searching directory: {exc}"
        except OSError as exc:
            return f"Failed to search code: {exc}"

        if not results:
            return (
                f"No matches found for keyword: {query}\n"
                f"Searched files: {searched_file_count}"
            )

        summary = (
            f"\n\nFound {len(results)} result(s); "
            f"searched {searched_file_count} file(s)"
        )

        if skipped_file_count:
            summary += f"; skipped {skipped_file_count} unreadable file(s)"

        if len(results) >= max_results:
            summary += f"; truncated at {max_results} result(s)"

        return "\n".join(results) + summary
