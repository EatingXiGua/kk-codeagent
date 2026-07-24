from typing import Any

from tools.base_tool import BaseTool
from workspace.workspace import Workspace


class WriteFileTool(BaseTool):
    """
    在工作区内创建或覆盖文本文件。
    """

    name = "write_file"
    description = "在工作区内创建文件或用新内容覆盖已有文件"

    def __init__(
        self,
        workspace: Workspace,
        max_content_length: int = 1_000_000,
    ):
        self.workspace = workspace
        self.max_content_length = max_content_length

    def execute(
        self,
        path: str,
        content: str,
        overwrite: bool = True,
        **kwargs: Any,
    ) -> str:
        """
        写入文件。

        :param path: 相对于工作区的文件路径
        :param content: 要写入的完整文件内容
        :param overwrite: 文件存在时是否允许覆盖
        """
        if not isinstance(content, str):
            return "参数错误：content 必须是字符串"

        if len(content) > self.max_content_length:
            return (
                "写入失败：文件内容过大，"
                f"最大允许 {self.max_content_length} 个字符"
            )

        file_path = self.workspace.resolve_path(path) # 绝对路径

        if file_path.exists() and file_path.is_dir():
            return f"写入失败：指定路径是目录：{path}"

        if file_path.exists() and not overwrite:
            return (
                f"写入失败：文件已经存在且 overwrite=false："
                f"{path}"
            )

        # 记录文件是否存在 在写入前文件是否已经存在 用于后续判断是创建还是覆盖
        existed_before = file_path.exists()

        try:
            file_path.parent.mkdir( # 创建父目录
                parents=True, # 如果父目录不存在，递归创建所有缺失的父目录
                exist_ok=True, # 如果目录已经存在，不报错
            )

            file_path.write_text( # 写文件
                content,
                encoding="utf-8",
            )

        except PermissionError as exc:
            return f"没有权限写入文件：{exc}"
        except OSError as exc:
            return f"写入文件失败：{exc}"

        action = "覆盖" if existed_before else "创建"

        line_count = len(content.splitlines())

        return (
            f"文件{action}成功：{path}\n"
            f"字符数：{len(content)}\n"
            f"行数：{line_count}"
        )

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": (
                                "相对于工作区根目录的文件路径，"
                                "例如 src/main.py"
                            ),
                        },
                        "content": {
                            "type": "string",
                            "description": (
                                "要写入文件的完整内容"
                            ),
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": (
                                "文件存在时是否允许覆盖，"
                                "默认为 true"
                            ),
                        },
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            },
        }