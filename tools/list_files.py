from typing import Any

from tools.base_tool import BaseTool
from workspace.workspace import Workspace

class ListFilesTool(BaseTool):
    """
    列出工作区中的文件和目录
    """
    name = "list_files"
    description = "列出工作区内指定目录中的文件和子目录"

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

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def execute(
            self,
            path: str = ".",
            recursive: bool = False,
            max_results: int = 200,
            **kwargs: Any,
    ) -> str:
        """
        列出指定目录中的内容
        :param path: 相对于工作区的目录路径
        :param recursive: 是否递归查找子目录
        :param max_results: 最大返回数量
        :param kwargs:
        :return:
        """
        if max_results <= 0:
            return "参数错误：max_results 必须大于 0"
        target_path = self.workspace.resolve_path(path) # 拿到绝对路径
        if not target_path.exists():
            return f"路径不存在：{path}"
        if not target_path.is_dir():
            return f"指定路径不是目录：{path}"
        iterator = ( # 值a if 条件 else 值b
            target_path.rglob("*") # rglob是Path对象的方法，意思是递归通配符匹配。* 表示匹配target_path下所有层级的文件和目录
            if recursive
            else target_path.iterdir() # iterdir是Path对象的方法，获取target_path目录第一层的内容
        )
        results: list[str] = []
        try:
            for item in iterator:
                # 只要路径中包含需要忽略的目录，就跳过
                if any( # any是python内置函数，接收一个可迭代对象（列表、元组、生成器），返回布尔值，只要有一个元素为true，就返回true
                    # 元素表达式 for 变量 in 可迭代对象
                    part in self.DEFAULT_IGNORED_NAMES # 检查这个元素是否在忽略集合中
                    for part in item.parts # 遍历item.parts中的每一个元素 item是一个Path对象，item.parts是这个路径的所有组成部分，是一个元组
                ):
                    continue

                relative_path = item.relative_to(self.workspace.root) # 计算相对路径

                if item.is_symlink(): # 检查路径是否是符号链接
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
                        f"结果数量超过 {max_results} 条，已截断"
                    )
                    break
        except PermissionError as exc:
            return f"没有权限读取目录：{exc}"
        except OSError as exc:
            return f"读取目录失败：{exc}"

        if not results:
            return f"目录为空：{path}"

        return "\n".join(results)

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
                                "相对于工作区根目录的目录路径，"
                                "例如 src 或 ."
                            ),
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": (
                                "是否递归列出所有子目录，"
                                "默认为 false"
                            ),
                        },
                        "max_results": {
                            "type": "integer",
                            "description": (
                                "最多返回多少条结果，默认为 200"
                            ),
                        },
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        }