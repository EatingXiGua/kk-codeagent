import fnmatch # python标准库，用于文件名匹配
from typing import Any

from tools.base_tool import BaseTool
from workspace.workspace import Workspace


class SearchCodeTool(BaseTool):
    """
    在工作区内搜索代码关键字。
    在指定的目录中查找所有符合条件的文件
    在这些文件中查找包含特定关键字的行
    返回匹配的行及其位置（文件路径+行号）
    """

    name = "search_code"
    description = "在工作区的文本文件中搜索指定关键字"

    # 默认忽略的目录名
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
    }

    # 默认文件匹配格式
    DEFAULT_FILE_PATTERNS = [
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

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def execute(
        self,
        query: str,
        path: str = ".",
        file_pattern: str | None = None,
        case_sensitive: bool = False,
        max_results: int = 100,
        **kwargs: Any,
    ) -> str:
        """
        搜索代码。

        :param query: 搜索关键字
        :param path: 搜索目录
        :param file_pattern: 文件匹配模式，例如 *.py
        :param case_sensitive: 是否区分大小写
        :param max_results: 最大结果数量
        """
        if not query:
            return "参数错误：query 不能为空"

        if max_results <= 0:
            return "参数错误：max_results 必须大于 0"

        search_root = self.workspace.resolve_path(path) # 绝对路径

        if not search_root.exists():
            return f"搜索路径不存在：{path}"

        if not search_root.is_dir():
            return f"搜索路径不是目录：{path}"

        # 确认文件匹配格式
        patterns = (
            [file_pattern] # 将单个字符串转为列表
            if file_pattern
            else self.DEFAULT_FILE_PATTERNS
        )

        # 根据是否区分大小写，转换搜索关键字
        target_query = (
            query
            if case_sensitive
            else query.lower()
        )

        results: list[str] = [] # 存储匹配的结果行
        searched_file_count = 0 # 统计搜索了多少个文件
        skipped_file_count = 0 # 统计跳过了多少个无法读取的文件

        try:
            for file_path in search_root.rglob("*"): # rglob("*") 递归遍历目录下的所有文件和目录
                if not file_path.is_file(): # 跳过目录
                    continue

                if file_path.is_symlink(): # 跳过符号链接
                    continue

                if any( # 如果路径的任何一级在忽略列表中，跳过这个文件
                    part in self.DEFAULT_IGNORED_NAMES # 如果part是默认忽略名称
                    for part in file_path.parts # part是file_path路径的每个部分
                ):
                    continue

                if not any( # 如果所有的格式都不匹配，就跳过这个文件
                    fnmatch.fnmatch(file_path.name, pattern) # 检查文件名是否匹配通配符格式 例如fnmatch.fnmatch("main.py", "*.py") True
                    for pattern in patterns # 遍历格式
                ):
                    continue

                searched_file_count += 1 # 每通过一个文件，计数器加1

                try:
                    content = file_path.read_text( # 读文件内容
                        encoding="utf-8",
                        errors="ignore",
                    )
                except (PermissionError, OSError): # 捕获到异常，统计跳过数量，跳过这个文件
                    skipped_file_count += 1
                    continue

                for line_number, line in enumerate( # 遍历每行，同时获取行号和行内容
                    content.splitlines(),
                    start=1,
                ):
                    compared_line = ( # 准备用于比较的行
                        line
                        if case_sensitive
                        else line.lower()
                    )

                    if target_query not in compared_line: # 如果搜索关键字不在用于比较的行中，跳过
                        continue

                    relative_path = file_path.relative_to(self.workspace.root) # 相对路径

                    stripped_line = line.strip() # 去掉行首行尾的空白字符

                    # 防止单行内容过长，占用太多上下文
                    if len(stripped_line) > 300:
                        stripped_line = (
                            stripped_line[:300] + "..."
                        )

                    results.append(
                        f"{relative_path}:{line_number}: "
                        f"{stripped_line}"
                    )

                    if len(results) >= max_results:
                        break

                if len(results) >= max_results:
                    break

        except PermissionError as exc:
            return f"没有权限搜索目录：{exc}"
        except OSError as exc:
            return f"搜索代码失败：{exc}"

        if not results:
            return (
                f"没有找到关键字：{query}\n"
                f"已搜索文件数：{searched_file_count}"
            )

        result_text = "\n".join(results)

        summary = (
            f"\n\n共找到 {len(results)} 条结果，"
            f"搜索了 {searched_file_count} 个文件"
        )

        if skipped_file_count:
            summary += (
                f"，跳过了 {skipped_file_count} 个无法读取的文件"
            )

        if len(results) >= max_results:
            summary += f"，结果已按 {max_results} 条截断"

        return result_text + summary

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "需要搜索的代码关键字，"
                                "例如 UserService 或 login"
                            ),
                        },
                        "path": {
                            "type": "string",
                            "description": (
                                "相对于工作区的搜索目录，"
                                "默认为整个工作区"
                            ),
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": (
                                "可选的文件匹配模式，"
                                "例如 *.py、*.java"
                            ),
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": (
                                "是否区分英文字母大小写，"
                                "默认为 false"
                            ),
                        },
                        "max_results": {
                            "type": "integer",
                            "description": (
                                "最大返回结果数量，"
                                "默认为 100"
                            ),
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        }