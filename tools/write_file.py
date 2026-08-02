from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from workspace.workspace import Workspace


class WriteFileInput(BaseModel):
    path: str = Field(
        description="File path relative to the workspace root.",
    )
    content: str = Field(
        description="Full text content to write.",
    )
    overwrite: bool = Field(
        default=True,
        description="Whether to overwrite an existing file.",
    )


class WriteFileTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "write_file"
    description: str = "Create or overwrite a text file in the workspace."
    args_schema: type[BaseModel] = WriteFileInput

    workspace: Workspace
    max_content_length: int = 1_000_000

    def _run(
        self,
        path: str,
        content: str,
        overwrite: bool = True,
    ) -> str:
        if len(content) > self.max_content_length:
            return (
                "Write failed: content is too large; "
                f"maximum is {self.max_content_length} characters."
            )

        file_path = self.workspace.resolve_path(path)

        if file_path.exists() and file_path.is_dir():
            return f"Write failed: path is a directory: {path}"

        if file_path.exists() and not overwrite:
            return (
                "Write failed: file already exists and overwrite=false: "
                f"{path}"
            )

        existed_before = file_path.exists()

        try:
            file_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            file_path.write_text(
                content,
                encoding="utf-8",
            )
        except PermissionError as exc:
            return f"Permission denied while writing file: {exc}"
        except OSError as exc:
            return f"Failed to write file: {exc}"

        action = "overwritten" if existed_before else "created"
        line_count = len(content.splitlines())

        return (
            f"File {action} successfully: {path}\n"
            f"Characters: {len(content)}\n"
            f"Lines: {line_count}"
        )
