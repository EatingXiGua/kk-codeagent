import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from agent import LangGraphSWEAgent
from graph import build_swe_graph
from llm import create_langchain_moonshot
from observability import get_langsmith_status
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


def build_tool_manager(workspace: Workspace) -> ToolManager:
    return ToolManager([
        ListFilesTool(workspace),
        ReadFileTool(workspace),
        SearchCodeTool(workspace),
        WriteFileTool(workspace),
        RunCommandTool(workspace),
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the SWE Agent in the current project workspace.",
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="Task for the agent. If omitted, you will be prompted.",
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root path. Defaults to the current directory.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=int(os.getenv("SWE_AGENT_MAX_STEPS", "10")),
        help="Maximum agent loop steps. Defaults to SWE_AGENT_MAX_STEPS or 10.",
    )
    parser.add_argument(
        "--langsmith-status",
        action="store_true",
        help="Show LangSmith tracing configuration and exit.",
    )
    return parser.parse_args()


def get_task(args: argparse.Namespace) -> str:
    if args.task:
        return " ".join(args.task).strip()

    return input("请输入任务：").strip()


def build_agent(
    tool_manager: ToolManager,
    max_steps: int,
) -> LangGraphSWEAgent:
    model = create_langchain_moonshot()
    tools = build_langchain_tools(tool_manager)
    graph = build_swe_graph(model, tools)
    return LangGraphSWEAgent(
        graph=graph,
        max_steps=max_steps,
    )


def main() -> None:
    load_dotenv()

    args = parse_args()

    if args.langsmith_status:
        status = get_langsmith_status()
        print("LangSmith status:")
        for key, value in status.items():
            print(f"{key}: {value}")
        return

    task = get_task(args)

    if not task:
        raise ValueError("任务不能为空")

    workspace_path = Path(args.workspace).resolve()
    workspace = Workspace(str(workspace_path))
    tool_manager = build_tool_manager(workspace)
    agent = build_agent(
        tool_manager=tool_manager,
        max_steps=args.max_steps,
    )

    result = agent.run(task)

    print("\n========== Agent 最终结果 ==========\n")
    print(result)


if __name__ == "__main__":
    main()
