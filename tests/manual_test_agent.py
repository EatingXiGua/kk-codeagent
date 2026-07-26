from agent import SWEAgent
from llm import MoonshotLLMClient
from tools import (
    ListFilesTool,
    ReadFileTool,
    RunCommandTool,
    SearchCodeTool,
    ToolManager,
    WriteFileTool,
)
from workspace.workspace import Workspace


def main():
    workspace = Workspace(
        "D:/pythonproject/sweagent"
    )

    tool_manager = ToolManager([
        ListFilesTool(workspace),
        ReadFileTool(workspace),
        SearchCodeTool(workspace),
        WriteFileTool(workspace),
        RunCommandTool(workspace),
    ])

    llm_client = MoonshotLLMClient()

    agent = SWEAgent(
        llm_client=llm_client,
        tool_manager=tool_manager,
        max_steps=10,
    )

    result = agent.run(
        "查看当前工作区的目录结构，"
        "告诉我有哪些主要的 Python 模块。"
        "这次不要修改任何文件。"
    )

    print("\n========== Agent 最终结果 ==========\n")
    print(result)


if __name__ == "__main__":
    main()