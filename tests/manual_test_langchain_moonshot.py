import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import HumanMessage, SystemMessage

from llm.langchain_moonshot import create_langchain_moonshot
from tools import (
    ListFilesTool,
    ReadFileTool,
    ToolManager,
    build_langchain_tools,
)
from workspace.workspace import Workspace


def main() -> None:
    model = create_langchain_moonshot()

    print("\n--- plain chat ---")
    plain_response = model.invoke([
        SystemMessage(content="You are a concise assistant."),
        HumanMessage(content="用一句话回答：2 + 2 等于多少？"),
    ])
    print(plain_response.content)

    print("\n--- tool binding ---")
    workspace = Workspace(".")
    tool_manager = ToolManager([
        ListFilesTool(workspace),
        ReadFileTool(workspace),
    ])
    tools = build_langchain_tools(tool_manager)
    model_with_tools = model.bind_tools(tools)

    tool_response = model_with_tools.invoke([
        SystemMessage(
            content=(
                "You are a software engineering agent. "
                "Use tools when you need workspace information."
            )
        ),
        HumanMessage(
            content=(
                "请调用 list_files 工具查看当前工作区根目录，"
                "不要直接猜测目录内容。"
            )
        ),
    ])

    print("content:", tool_response.content)
    print("tool_calls:", tool_response.tool_calls)


if __name__ == "__main__":
    main()
