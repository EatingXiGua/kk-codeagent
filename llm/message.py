from dataclasses import dataclass, field
from typing import Any

"""
    定义模型响应的两种数据格式
"""

@dataclass # dataclass 装饰器，自动生成 __init__、__repr__、__eq__ 等方法
class ToolCall:
    """
    大模型返回的一次工具调用。

    例如模型决定调用：

    read_file(
        path="src/main.py",
        start_line=1,
        end_line=100
    )
    """

    # 本次工具调用的唯一 ID
    id: str

    # 工具名称，例如 read_file
    name: str

    # 工具参数
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """
    对大模型响应结果进行统一封装。

    大模型可能返回两类结果：

    1. 普通文本
    2. 工具调用
    """

    # 模型的普通文本响应模型
    content: str | None = None

    # 模型响应要求执行的工具，一次响应可能包括多个工具调用
    tool_calls: list[ToolCall] = field( # field保证每个实例都有自己的独立列表
        default_factory=list
    )

    # 原始模型响应，方便调试
    raw_response: Any = None

    @property # property的作用是将方法变为属性，调用的时候不需要括号
    def has_tool_calls(self) -> bool:
        """
        判断模型是否要求调用工具。
        """
        return len(self.tool_calls) > 0