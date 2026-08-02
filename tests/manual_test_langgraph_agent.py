import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent import LangGraphSWEAgent
from graph import build_swe_graph
from llm import create_langchain_moonshot
from tools import (
    ListFilesTool,
    ReadFileTool,
    ToolManager,
    build_langchain_tools,
)
from workspace.workspace import Workspace


def main() -> None:
    workspace = Workspace(".")
    tool_manager = ToolManager([
        ListFilesTool(workspace),
        ReadFileTool(workspace),
    ])
    tools = build_langchain_tools(tool_manager)

    model = create_langchain_moonshot()
    graph = build_swe_graph(model, tools)
    agent = LangGraphSWEAgent(graph)

    result = agent.run(
        "请调用 list_files 工具查看当前工作区根目录，"
        "然后用一句话总结主要目录。"
    )

    print(result)


if __name__ == "__main__":
    main()
