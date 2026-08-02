from typing import Any

from langchain_core.messages import AIMessage

from graph import build_swe_graph
from tools import ListFilesTool
from workspace.workspace import Workspace


class FakeModel:
    def bind_tools(self, tools: list[Any]) -> "FakeModel":
        self.bound_tools = tools
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        return AIMessage(content="done")


def test_build_swe_graph_compiles(tmp_path):
    workspace = Workspace(str(tmp_path))
    tools = [
        ListFilesTool(workspace=workspace),
    ]

    graph = build_swe_graph(FakeModel(), tools)

    assert graph is not None
    assert type(graph).__name__ == "CompiledStateGraph"
