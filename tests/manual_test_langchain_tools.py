import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import (
    ListFilesTool,
    ReadFileTool,
    RunCommandTool,
    SearchCodeTool,
    ToolManager,
    WriteFileTool,
)
from tools.langchain_tools import build_langchain_tools
from workspace.workspace import Workspace


def main() -> None:
    workspace = Workspace(".")
    tool_manager = ToolManager([
        ListFilesTool(workspace),
        ReadFileTool(workspace),
        SearchCodeTool(workspace),
        WriteFileTool(workspace),
        RunCommandTool(workspace),
    ])

    tools = {
        tool.name: tool
        for tool in build_langchain_tools(tool_manager)
    }

    print("\n--- list_files ---")
    print(tools["list_files"].invoke({
        "path": ".",
        "recursive": False,
        "max_results": 20,
    }))

    print("\n--- read_file ---")
    print(tools["read_file"].invoke({
        "path": "main.py",
        "start_line": 1,
        "end_line": 8,
    }))

    print("\n--- search_code ---")
    print(tools["search_code"].invoke({
        "query": "class LangGraphSWEAgent",
        "path": "agent",
        "file_pattern": "*.py",
        "max_results": 5,
    }))

    print("\n--- write_file ---")
    print(tools["write_file"].invoke({
        "path": "workspace/langchain_tool_test.txt",
        "content": "hello langchain tools\n",
        "overwrite": True,
    }))

    print("\n--- run_command ---")
    print(tools["run_command"].invoke({
        "command": "python --version",
        "timeout": 10,
    }))


if __name__ == "__main__":
    main()
