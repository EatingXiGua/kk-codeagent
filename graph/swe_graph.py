from typing import Any

from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


def build_swe_graph(model: Any, tools: list[Any]) -> Any:
    model_with_tools = model.bind_tools(tools)

    def agent_node(state: MessagesState) -> dict[str, list[Any]]:
        response = model_with_tools.invoke(state["messages"])
        return {
            "messages": [response],
        }

    graph_builder = StateGraph(MessagesState)

    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", tools_condition)
    graph_builder.add_edge("tools", "agent")

    return graph_builder.compile()
