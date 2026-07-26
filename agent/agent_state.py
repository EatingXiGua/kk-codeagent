from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """
    保存 Agent 执行任务时的状态。

    messages 是最重要的字段，它保存：
    - 系统提示词
    - 用户任务
    - 模型回复
    - 模型工具调用
    - 工具执行结果

    每次调用模型时，都把完整 messages 传给模型，
    模型才知道之前发生过什么。
    """

    # 用户最开始提交的任务
    task: str

    # 对话和工具执行历史
    messages: list[dict[str, Any]] = field(
        default_factory=list
    )

    # 已经执行了多少轮
    step_count: int = 0

    # 是否已经结束
    finished: bool = False

    # 最终返回给用户的答案
    final_answer: str | None = None