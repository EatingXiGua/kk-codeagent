from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agent.prompts import SYSTEM_PROMPT
from observability import traceable


class LangGraphSWEAgent:
    def __init__(
        self,
        graph: Any,
        max_steps: int = 30,
    ):
        if max_steps <= 0:
            raise ValueError("max_steps must be greater than 0")

        self.graph = graph
        self.max_steps = max_steps

    @traceable(
        name="LangGraphSWEAgent.run",
        run_type="chain",
        tags=["sweagent", "langgraph"],
    )
    def run(self, task: str) -> str:
        if not task or not task.strip():
            raise ValueError("task cannot be empty")

        result = self.graph.invoke({
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=task.strip()),
            ],
        }, config={
            "recursion_limit": self.max_steps,
        })

        messages = result.get("messages", [])

        if not messages:
            return "LangGraph agent finished without messages."

        final_message = messages[-1]
        content = getattr(final_message, "content", None)

        if isinstance(content, str) and content.strip():
            return content

        return "LangGraph agent finished without a final answer."
