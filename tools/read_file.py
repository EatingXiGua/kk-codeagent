from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from workspace.workspace import Workspace


class ReadFileInput(BaseModel):
    path: str = Field(
        description="File path relative to the workspace root.",
    )
    start_line: int = Field(
        default=1,
        ge=1,
        description="First line to read, starting from 1.",
    )
    end_line: int | None = Field(
        default=None,
        description="Last line to read, inclusive.",
    )


class ReadFileTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "read_file"
    description: str = "Read a text file in the workspace with line numbers."
    args_schema: type[BaseModel] = ReadFileInput

    workspace: Workspace
    default_max_lines: int = 300

    def _run(
        self,
        path: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> str:
        if end_line is not None and end_line < start_line:
            return "Invalid arguments: end_line cannot be less than start_line"

        file_path = self.workspace.resolve_path(path)

        if not file_path.exists():
            return f"File does not exist: {path}"

        if not file_path.is_file():
            return f"Path is not a file: {path}"

        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except PermissionError as exc:
            return f"Permission denied while reading file: {exc}"
        except OSError as exc:
            return f"Failed to read file: {exc}"

        lines = content.splitlines()
        total_lines = len(lines)

        if total_lines == 0:
            return f"File is empty: {path}"

        if start_line > total_lines:
            return (
                f"Start line {start_line} is out of range; "
                f"file has {total_lines} lines."
            )

        actual_end_line = (
            min(start_line + self.default_max_lines - 1, total_lines)
            if end_line is None
            else min(end_line, total_lines)
        )
        selected_lines = lines[start_line - 1:actual_end_line]
        line_number_width = len(str(actual_end_line))

        result_lines = [
            f"{line_number:>{line_number_width}} | {line_content}"
            for line_number, line_content in enumerate(
                selected_lines,
                start=start_line,
            )
        ]

        header = (
            f"File: {path}\n"
            f"Lines: {start_line}-{actual_end_line}; "
            f"total lines: {total_lines}\n"
        )

        footer = ""
        if actual_end_line < total_lines:
            footer = (
                "\n\nFile content is not fully read; "
                f"continue from line {actual_end_line + 1}."
            )

        return header + "\n".join(result_lines) + footer
