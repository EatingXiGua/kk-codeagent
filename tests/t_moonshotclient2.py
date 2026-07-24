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

    client = MoonshotLLMClient()

    response = client.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个软件工程 Agent。"
                    "用户要求查看目录时，"
                    "必须调用 list_files 工具，"
                    "不要自己猜测目录内容。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请查看当前工作区根目录有哪些文件。"
                ),
            },
        ],
        tools=tool_manager.get_schemas(),
    )

    print("模型文本：")
    print(response.content)

    print("\n是否请求调用工具：")
    print(response.has_tool_calls)

    for tool_call in response.tool_calls:
        print("\n工具调用 ID：")
        print(tool_call.id)

        print("\n工具名称：")
        print(tool_call.name)

        print("\n工具参数：")
        print(tool_call.arguments)

        tool_result = tool_manager.execute(
            tool_call.name,
            tool_call.arguments,
        )

        print("\n工具执行结果：")
        print(tool_result)


if __name__ == "__main__":
    main()