from tools import (
    ListFilesTool,
    ReadFileTool,
    RunCommandTool,
    SearchCodeTool,
    ToolManager,
    WriteFileTool,
)
from workspace.workspace import Workspace


workspace = Workspace(
    "D:/pythonproject/sweagent/tests"
)

tool_manager = ToolManager([
    ListFilesTool(workspace),
    ReadFileTool(workspace),
    SearchCodeTool(workspace),
    WriteFileTool(workspace),
    RunCommandTool(workspace),
])

if __name__ == "__main__":
    print("1111")
    print(tool_manager.get_tool_names())