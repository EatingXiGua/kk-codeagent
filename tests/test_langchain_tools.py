from pathlib import Path

from tools import (
    ListFilesTool,
    ReadFileTool,
    RunCommandTool,
    SearchCodeTool,
    WriteFileTool,
)
from workspace.workspace import Workspace


def build_test_tools(tmp_path: Path):
    workspace = Workspace(str(tmp_path))

    return [
        ListFilesTool(workspace=workspace),
        ReadFileTool(workspace=workspace),
        SearchCodeTool(workspace=workspace),
        WriteFileTool(workspace=workspace),
        RunCommandTool(workspace=workspace),
    ]


def test_langchain_tools_have_all_tool_names(
    tmp_path: Path,
):
    tools = build_test_tools(tmp_path)

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
    (tmp_path / ".env").write_text(
        "SECRET=value\n",
        encoding="utf-8",
    )

    test_tools = build_test_tools(tmp_path)
    tools = {
        tool.name: tool
        for tool in test_tools
    }

    result = tools["list_files"].invoke({
        "path": ".",
        "recursive": False,
        "max_results": 20,
    })

    assert "[FILE] main.py" in result
    assert ".env" not in result
