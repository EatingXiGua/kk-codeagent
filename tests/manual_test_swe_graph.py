import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import HumanMessage, SystemMessage

from agent.prompts import SYSTEM_PROMPT
from graph import build_swe_graph
from llm import create_langchain_moonshot
from tools import (
    ListFilesTool,
    ReadFileTool,
)
from workspace.workspace import Workspace


def main() -> None:
    workspace = Workspace(".")
    tools = [
        ListFilesTool(workspace=workspace),
        ReadFileTool(workspace=workspace),
    ]

    model = create_langchain_moonshot()
    graph = build_swe_graph(model, tools)

    result = graph.invoke({
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "请调用 list_files 工具查看当前工作区根目录，"
                    "然后用一句话总结你看到了哪些主要目录。"
                )
            ),
        ],
    })

    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
