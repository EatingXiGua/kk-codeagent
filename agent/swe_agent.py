import json
from typing import Any

from agent.agent_state import AgentState # agent状态
from agent.prompts import SYSTEM_PROMPT # 系统提示词
from llm.llm_client import LLMClient # 大模型客户端基类
from llm.message import LLMResponse, ToolCall # 大模型响应统一格式 工具调用请求
from tools.tool_manager import ToolManager # 工具类管理
from agent.logger import AgentLogger


class SWEAgent:
    """
    SWE Agent 主类。

    它负责不断执行：

    模型思考
        ↓
    调用工具
        ↓
    获得工具结果
        ↓
    把结果重新发送给模型

    直到模型不再调用工具，而是返回最终答案。
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_manager: ToolManager,
        max_steps: int = 30,
        logger: AgentLogger | None = None,
    ):
        if max_steps <= 0:
            raise ValueError(
                "max_steps 必须大于 0"
            )

        self.llm_client = llm_client
        self.tool_manager = tool_manager
        self.max_steps = max_steps
        self.logger = logger or AgentLogger()

    def run(self, task: str) -> str:
        """
        执行用户任务。

        :param task: 用户交给 Agent 的软件工程任务
        :return: Agent 最终答案
        """
        if not task or not task.strip():
            raise ValueError(
                "task 不能为空"
            )

        state = self._create_initial_state( # 创建一个AgentState
            task.strip()
        )

        while ( # 主循环
            not state.finished
            and state.step_count < self.max_steps
        ):
            state.step_count += 1
            self.logger.log_step(state.step_count)

            response = self.llm_client.chat( # 调用模型 发送消息历史和工具给大模型
                messages=state.messages,
                tools=self.tool_manager.get_schemas(),
            )
            self.logger.log_model_content(response.content)

            # 先把模型本轮回复放入消息历史 构建assistant消息
            assistant_message = (
                self._build_assistant_message(response)
            )

            state.messages.append( # 把大模型的回复加入消息历史
                assistant_message
            )

            # 模型没有调用工具，表示它认为任务已经完成
            if not response.has_tool_calls:
                state.finished = True
                state.final_answer = (
                    response.content
                    or "模型没有返回最终答案。"
                )
                self.logger.log_finished(state.final_answer)
                break

            # 模型请求调用一个或多个工具
            for tool_call in response.tool_calls:
                tool_result = (
                    self.tool_manager.execute(
                        tool_call.name,
                        tool_call.arguments,
                    )
                )
                self.logger.log_tool_result(tool_name=tool_call.name,result=tool_result,)

                # 工具执行结果也要放回消息历史
                state.messages.append(
                    self._build_tool_result_message(
                        tool_call=tool_call,
                        result=tool_result,
                    )
                )

        if not state.finished:
            return (
                f"Agent 已达到最大执行轮数 "
                f"{self.max_steps}，任务尚未完成。"
            )

        return (
            state.final_answer
            or "任务结束，但没有最终答案。"
        )

    @staticmethod
    def _create_initial_state(
        task: str,
    ) -> AgentState:
        """
        创建 Agent 初始状态。
        """
        return AgentState(
            task=task,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": task,
                },
            ],
        )

    @staticmethod
    def _build_assistant_message(
        response: LLMResponse,
    ) -> dict[str, Any]:
        """
        将项目内部的 LLMResponse 转换成模型接口要求的
        assistant 消息格式。

        普通回答示例：

        {
            "role": "assistant",
            "content": "任务已经完成"
        }

        工具调用示例：

        {
            "role": "assistant",
            "content": null,
            "tool_calls": [...]
        }
        """
        message: dict[str, Any] = {
            "role": "assistant",
            "content": response.content,
        }

        if response.tool_calls:
            message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": json.dumps(
                            tool_call.arguments,
                            ensure_ascii=False,
                        ),
                    },
                }
                for tool_call in response.tool_calls
            ]

        return message

    @staticmethod
    def _build_tool_result_message(
        tool_call: ToolCall,
        result: str,
    ) -> dict[str, Any]:
        """
        将工具执行结果转换成模型接口要求的 tool 消息。

        tool_call_id 必须和模型发起工具调用时的 ID 一致，
        模型才能知道这个结果对应哪次工具调用。
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        }