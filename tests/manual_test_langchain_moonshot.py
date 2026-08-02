import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import HumanMessage, SystemMessage

from llm.langchain_moonshot import create_langchain_moonshot
from tools import ListFilesTool, ReadFileTool
from workspace.workspace import Workspace


def main() -> None:
    model = create_langchain_moonshot()

    print("\n--- plain chat ---")
    plain_response = model.invoke([
        SystemMessage(content="You are a concise assistant."),
        HumanMessage(content="Answer in one sentence: what is 2 + 2?"),
    ])
    print(plain_response.content)

    print("\n--- tool binding ---")
    workspace = Workspace(".")
    tools = [
        ListFilesTool(workspace=workspace),
        ReadFileTool(workspace=workspace),
    ]
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
                "Call the list_files tool to inspect the workspace root. "
                "Do not guess the directory contents."
            )
        ),
    ])

    print("content:", tool_response.content)
    print("tool_calls:", tool_response.tool_calls)


if __name__ == "__main__":
    main()
