from typing import Any

from tools.base_tool import BaseTool
from workspace.workspace import Workspace


class ReadFileTool(BaseTool):
    """
    读取工作区内的文本文件。
    """

    name = "read_file"
    description = "读取工作区内指定文本文件的内容，并显示行号"

    def __init__(
        self,
        workspace: Workspace,
        default_max_lines: int = 300,
    ):
        self.workspace = workspace
        self.default_max_lines = default_max_lines

    def execute(
        self,
        path: str,
        start_line: int = 1,
        end_line: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        读取文件指定范围的内容。

        :param path: 相对于工作区的文件路径
        :param start_line: 开始行，行号从 1 开始
        :param end_line: 结束行，包含该行
        """
        if start_line < 1:
            return "参数错误：start_line 必须大于或等于 1"

        if end_line is not None and end_line < start_line:
            return "参数错误：end_line 不能小于 start_line"

        file_path = self.workspace.resolve_path(path)

        if not file_path.exists():
            return f"文件不存在：{path}"

        if not file_path.is_file():
            return f"指定路径不是文件：{path}"

        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except PermissionError as exc:
            return f"没有权限读取文件：{exc}"
        except OSError as exc:
            return f"读取文件失败：{exc}"

        lines = content.splitlines() # 按换行符分割字符串，返回字符串列表

        total_lines = len(lines)

        if total_lines == 0:
            return f"文件为空：{path}"

        if start_line > total_lines:
            return (
                f"开始行 {start_line} 超出文件范围，"
                f"文件共有 {total_lines} 行"
            )

        # 如果没有传 end_line，默认只读取一定数量的行
        if end_line is None:
            actual_end_line = min(
                start_line + self.default_max_lines - 1,
                total_lines,
            )
        else:
            actual_end_line = min(end_line, total_lines)

        # 提取指定范围的行
        selected_lines = lines[
            start_line - 1:actual_end_line
        ]
        # 计算行号宽度 作用：让行号右对齐，美观
        line_number_width = len(str(actual_end_line))

        result_lines = []

        for line_number, line_content in enumerate(
            selected_lines,
            start=start_line, # enumerate同时获取索引和值，索引从start_line开始
        ):
            result_lines.append(
                f"{line_number:>{line_number_width}} | " # :表示格式化开始 >表示右对齐 例如5:3输出"  5"，前面两个空格
                f"{line_content}"
            )

        header = (
            f"文件：{path}\n"
            f"行范围：{start_line}-{actual_end_line}，"
            f"总行数：{total_lines}\n"
        )

        if actual_end_line < total_lines:
            footer = (
                "\n\n文件内容尚未读取完毕，"
                f"下一次可以从第 {actual_end_line + 1} 行继续读取。"
            )
        else:
            footer = ""

        return header + "\n".join(result_lines) + footer

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
                        "start_line": {
                            "type": "integer",
                            "description": (
                                "开始读取的行号，从 1 开始，"
                                "默认为 1"
                            ),
                        },
                        "end_line": {
                            "type": "integer",
                            "description": (
                                "结束读取的行号，包含这一行；"
                                "不传时默认读取最多 300 行"
                            ),
                        },
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        }