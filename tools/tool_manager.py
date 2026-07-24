import json
from typing import Any

from tools.base_tool import BaseTool


class ToolManager:
    """
    工具管理器。

    主要职责：
    1. 注册工具
    2. 根据名称查找工具
    3. 执行工具
    4. 向大模型提供所有工具的 Schema
    """

    def __init__(
        self,
        tools: list[BaseTool] | None = None,
    ):
        self._tools: dict[str, BaseTool] = {} # 字典：工具名称-工具类 _下划线开头表示这是一个私有属性

        if tools: # 如果传入了工具列表，遍历列表，逐个调用register方法
            for tool in tools:
                self.register(tool)

    def register(self, tool: BaseTool) -> None:
        """
        注册一个工具。
        """
        if not tool.name:
            raise ValueError("工具名称不能为空")

        if tool.name in self._tools:
            raise ValueError(
                f"工具已经注册：{tool.name}"
            )

        self._tools[tool.name] = tool # 把工具添加到字典

    def get_tool(self, tool_name: str) -> BaseTool | None:
        """
        根据名称获取工具。
        """
        return self._tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        """
        判断指定工具是否已注册。
        """
        return tool_name in self._tools

    def execute(
        self,
        tool_name: str, # 要执行的工具名称
        arguments: dict[str, Any] | str | None = None, # 工具的参数  例如{"path": "main.py", "start_line": 1}
    ) -> str:
        """
        执行指定工具。

        arguments 既支持字典，也支持模型返回的 JSON 字符串。
        """
        tool = self.get_tool(tool_name)

        if tool is None:
            return (
                f"未知工具：{tool_name}\n"
                f"可用工具：{', '.join(self.get_tool_names())}"
            )

        try:
            parsed_arguments = self._parse_arguments(arguments) # _parse_arguments将参数统一转为字典

            return tool.execute(**parsed_arguments) # 执行工具

        except json.JSONDecodeError as exc: # json解析错误
            return (
                f"工具参数不是合法 JSON：{tool_name}\n"
                f"错误信息：{exc}"
            )

        except TypeError as exc: # 参数类型错误
            return (
                f"工具参数错误：{tool_name}\n"
                f"错误信息：{exc}"
            )

        except Exception as exc:
            # 工具异常不直接让整个 Agent 崩溃，
            # 而是把错误信息返回给大模型继续处理。
            return (
                f"工具执行失败：{tool_name}\n"
                f"错误类型：{type(exc).__name__}\n"
                f"错误信息：{exc}"
            )

    def get_schemas(self) -> list[dict[str, Any]]:
        """
        返回所有工具的 Schema。
        """
        return [
            tool.get_schema()
            for tool in self._tools.values()
        ]

    def get_tool_names(self) -> list[str]:
        """
        返回所有已注册的工具名称。
        """
        return list(self._tools.keys())

    @staticmethod
    def _parse_arguments(
        arguments: dict[str, Any] | str | None,
    ) -> dict[str, Any]:
        """
        将工具参数统一转换为字典。
        """
        if arguments is None:
            return {}

        if isinstance(arguments, dict):
            return arguments

        if isinstance(arguments, str): # 如果参数是字符串
            if not arguments.strip(): #且字符串是空白，返回空字典
                return {}

            parsed = json.loads(arguments) # 解析json字符串

            if not isinstance(parsed, dict): # 解析结果不是字典，抛异常
                raise TypeError(
                    "工具参数 JSON 的最外层必须是对象"
                )

            return parsed # 解析结果是字典，返回

        raise TypeError(
            "arguments 必须是字典、JSON 字符串或 None"
        )