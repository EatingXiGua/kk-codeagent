from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agent.prompts import SYSTEM_PROMPT
from observability import traceable


class LangGraphSWEAgent:
    def __init__(
        self,
        graph: Any,
    ):
        self.graph = graph

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
        })

        messages = result.get("messages", [])

        if not messages:
            return "LangGraph agent finished without messages."

        final_message = messages[-1]
        content = getattr(final_message, "content", None)

        if isinstance(content, str) and content.strip():
            return content

        return "LangGraph agent finished without a final answer."
