from pathlib import Path

from tools import (
    ListFilesTool,
    ReadFileTool,
    RunCommandTool,
    SearchCodeTool,
    ToolManager,
    WriteFileTool,
    build_langchain_tools,
)
from workspace.workspace import Workspace


def build_test_tool_manager(tmp_path: Path) -> ToolManager:
    workspace = Workspace(str(tmp_path))

    return ToolManager([
        ListFilesTool(workspace),
        ReadFileTool(workspace),
        SearchCodeTool(workspace),
        WriteFileTool(workspace),
        RunCommandTool(workspace),
    ])


def test_build_langchain_tools_has_all_tool_names(
    tmp_path: Path,
):
    tool_manager = build_test_tool_manager(tmp_path)

    tools = build_langchain_tools(tool_manager)

    tool_names = {
        tool.name
        for tool in tools
    }

    assert tool_names == {
        "list_files",
        "read_file",
        "search_code",
        "write_file",
        "run_command",
    }


def test_list_files_langchain_tool_can_invoke(
    tmp_path: Path,
):
    (tmp_path / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    tool_manager = build_test_tool_manager(tmp_path)
    tools = {
        tool.name: tool
        for tool in build_langchain_tools(tool_manager)
    }

    result = tools["list_files"].invoke({
        "path": ".",
        "recursive": False,
        "max_results": 20,
    })

    assert "[FILE] main.py" in result
