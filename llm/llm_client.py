from abc import ABC, abstractmethod
from typing import Any

from llm.message import LLMResponse


class LLMClient(ABC):
    """
    大模型客户端的抽象基类。

    后续可以实现：

    OpenAILLMClient
    DeepSeekLLMClient
    OllamaLLMClient
    """

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """
        调用大模型。

        :param messages:
            对话消息历史，例如：

            [
                {
                    "role": "system",
                    "content": "你是一个软件工程 Agent"
                },
                {
                    "role": "user",
                    "content": "读取 main.py"
                }
            ]

        :param tools:
            工具 Schema，由 ToolManager.get_schemas() 返回。

        :return:
            统一封装后的 LLMResponse
        """
        raise NotImplementedError