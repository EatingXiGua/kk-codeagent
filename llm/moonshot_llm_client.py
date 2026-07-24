import json # 解析json格式
import os # 读取环境变量
from typing import Any

from dotenv import load_dotenv # 加载.env文件中的环境变量
from openai import OpenAI # openai api 兼容moonshot api

from llm.llm_client import LLMClient
from llm.message import LLMResponse, ToolCall # 统一响应格式


class MoonshotLLMClient(LLMClient):
    """
    月之暗面 Kimi 模型客户端。

    主要职责：

    1. 从环境变量中读取 Moonshot API Key
    2. 调用 Kimi 模型
    3. 解析模型返回的普通文本
    4. 解析模型返回的工具调用
    5. 将结果封装成统一的 LLMResponse
    """

    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "kimi-k2.6"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
    ):
        """
        初始化 Moonshot 客户端。

        参数的读取优先级：

        1. 创建对象时显式传入的参数
        2. 操作系统环境变量
        3. 默认值

        :param api_key: Moonshot API Key
        :param model: 模型名称
        :param base_url: Moonshot API 地址
        :param timeout: 请求超时时间，单位为秒
        """

        # 加载项目根目录中的 .env 文件。
        # 即使你使用的是系统环境变量，保留这一行也没有问题。
        load_dotenv()

        self.api_key = (
            api_key
            or os.getenv("MOONSHOT_API_KEY")
        )

        self.model = (
            model
            or os.getenv("MOONSHOT_MODEL")
            or self.DEFAULT_MODEL
        )

        self.base_url = (
            base_url
            or os.getenv("MOONSHOT_BASE_URL")
            or self.DEFAULT_BASE_URL
        )

        if not self.api_key:
            raise ValueError(
                "没有读取到 Moonshot API Key。"
                "请配置环境变量 MOONSHOT_API_KEY。"
            )

        if timeout <= 0:
            raise ValueError(
                "timeout 必须大于 0"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=timeout,
        )

    def chat(
        self,
        messages: list[dict[str, Any]], # 对话消息列表
        tools: list[dict[str, Any]] | None = None, # 工具schema列表
    ) -> LLMResponse:
        """
        调用 Kimi 模型。

        :param messages:
            对话消息列表，例如：

            [
                {
                    "role": "system",
                    "content": "你是一个软件工程 Agent"
                },
                {
                    "role": "user",
                    "content": "查看项目目录"
                }
            ]

        :param tools:
            提供给模型的工具 Schema，
            通常来自 ToolManager.get_schemas()。

        :return:
            统一格式的 LLMResponse
        """

        if not messages:
            raise ValueError(
                "messages 不能为空"
            )

        request_parameters: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }

        # 只有真正传入工具时，才把 tools 发给模型。
        if tools:
            request_parameters["tools"] = tools
            request_parameters["tool_choice"] = "auto"

        response = self.client.chat.completions.create(
            **request_parameters
        )

        if not response.choices:
            raise RuntimeError(
                "Kimi 模型没有返回任何 choices"
            )

        response_message = response.choices[0].message

        tool_calls = self._parse_tool_calls(
            response_message.tool_calls
        )

        return LLMResponse(
            content=response_message.content,
            tool_calls=tool_calls,
            raw_response=response,
        )

    def _parse_tool_calls(
        self,
        raw_tool_calls: Any,
    ) -> list[ToolCall]:
        """
        解析 Kimi 返回的工具调用。

        模型原始返回结构大致为：

        tool_calls=[
            {
                "id": "call_xxx",
                "function": {
                    "name": "read_file",
                    "arguments": "{\"path\": \"main.py\"}"
                }
            }
        ]

        转换为项目内部统一的 ToolCall 对象。

        解析后的格式为：
        ToolCall(
            id="call_abc123",
            name="read_file",
            arguments={
                "path": "main.py",
                "start_line": 1
            }
        )
        """

        if not raw_tool_calls:
            return []

        parsed_tool_calls: list[ToolCall] = []

        for raw_tool_call in raw_tool_calls:
            function = raw_tool_call.function

            arguments = self._parse_tool_arguments(
                function.arguments
            )

            parsed_tool_calls.append(
                ToolCall(
                    id=raw_tool_call.id,
                    name=function.name,
                    arguments=arguments,
                )
            )

        return parsed_tool_calls

    @staticmethod
    def _parse_tool_arguments(
        arguments: str | None,
    ) -> dict[str, Any]:
        """
        将模型返回的 JSON 参数字符串转换为字典。

        例如模型返回：

        '{"path": "src/main.py", "start_line": 1}'

        转换后：

        {
            "path": "src/main.py",
            "start_line": 1
        }
        """

        if not arguments:
            return {}

        try:
            parsed_arguments = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Kimi 返回的工具参数不是合法 JSON："
                f"{arguments}"
            ) from exc

        if not isinstance(parsed_arguments, dict):
            raise ValueError(
                "工具参数 JSON 的最外层必须是对象"
            )

        return parsed_arguments