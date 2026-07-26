import os
import re
from typing import Any

from sandbox import CommandExecutor, CommandResult
from tools.base_tool import BaseTool
from workspace.workspace import Workspace


class RunCommandTool(BaseTool):
    """
    在工作区中执行命令。

    RunCommandTool 负责：
    1. 校验命令参数
    2. 检查命令白名单
    3. 检查危险命令
    4. 调用 CommandExecutor
    5. 格式化命令执行结果
    """

    name = "run_command"
    description = "在工作区根目录中执行测试、编译或代码检查命令"

    ALLOWED_EXECUTABLES = {
        "python",
        "python.exe",
        "python3",
        "pytest",
        "pytest.exe",
        "pip",
        "pip.exe",
        "pip3",
        "git",
        "git.exe",
        "mvn",
        "mvn.cmd",
        "mvnw",
        "mvnw.cmd",
        "gradle",
        "gradle.bat",
        "gradlew",
        "gradlew.bat",
        "npm",
        "npm.cmd",
        "npx",
        "npx.cmd",
        "node",
        "node.exe",
        "ruff",
        "ruff.exe",
        "black",
        "black.exe",
        "mypy",
        "mypy.exe",
    }

    # 阻止包含这些模式的命令 \b单词边界，匹配单词的开始或结束  \s+一个或多个空白字符    /正斜杠，Windows路径   [sq]匹配s或q
    DANGEROUS_PATTERNS = [
        r"\brm\s+-rf\b",
        r"\brmdir\s+/s\b",
        r"\bdel\s+/[sq]\b",
        r"\bformat\b",
        r"\bshutdown\b",
        r"\breboot\b",
        r"\bpoweroff\b",
        r"\bmkfs\b",
        r"\bdiskpart\b",
        r"\breg\s+delete\b",
        r"\bsudo\b",
        r"\bcurl\b",
        r"\bwget\b",
        r"\binvoke-webrequest\b",
        r"\bnet\s+user\b",
    ]

    def __init__(
        self,
        workspace: Workspace,
        default_timeout: int = 60,
        max_output_length: int = 20_000,
    ):
        self.workspace = workspace

        self.executor = CommandExecutor(
            working_directory=workspace.root,
            default_timeout=default_timeout,
            max_output_length=max_output_length,
        )

    def execute(
        self,
        command: str,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        执行命令。

        :param command:
            需要执行的命令

        :param timeout:
            超时时间，单位为秒
        """
        if not command or not command.strip():
            return "参数错误：command 不能为空"

        command = command.strip()

        validation_error = self._validate_command(
            command
        )

        if validation_error:
            return validation_error

        if timeout is not None:
            if timeout <= 0:
                return "参数错误：timeout 必须大于 0"

            if timeout > 600:
                return (
                    "参数错误：timeout 不能超过 600 秒"
                )

        result = self.executor.execute(
            command=command,
            timeout=timeout,
        )

        return self._format_result(result)

    def _validate_command(
        self,
        command: str,
    ) -> str | None:
        """
        对命令进行基础安全检查。
        """
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(
                pattern,
                command,
                flags=re.IGNORECASE,
            ):
                return (
                    "命令被拒绝："
                    "检测到危险命令或不允许的操作"
                )

        # 第一版禁止一次执行多个命令
        forbidden_separators = {
            "&&",
            "||",
            ";",
            "\n",
            "\r",
        }

        if any(
            separator in command
            for separator in forbidden_separators
        ):
            return (
                "命令被拒绝：第一版暂不允许使用 "
                "&&、||、分号或多行命令"
            )

        executable = self._extract_executable(
            command
        )

        if not executable:
            return (
                "命令被拒绝：无法识别可执行程序"
            )

        if executable.lower() not in {
            item.lower()
            for item in self.ALLOWED_EXECUTABLES
        }:
            return (
                f"命令被拒绝：不允许执行 {executable}\n"
                "允许的程序包括："
                + ", ".join(
                    sorted(self.ALLOWED_EXECUTABLES)
                )
            )

        return None

    @staticmethod
    def _extract_executable(
        command: str,
    ) -> str:
        """
        提取命令中的可执行程序名称。

        示例：

        python -m pytest
        返回 python

        "D:/AppDir/miniconda/envs/swe-agent/python.exe" -m pytest
        返回 python.exe
        """
        stripped_command = command.strip()

        if stripped_command.startswith('"'):
            closing_quote_index = (
                stripped_command.find('"', 1)
            )

            if closing_quote_index == -1:
                return ""

            executable_path = stripped_command[
                1:closing_quote_index
            ]
        elif stripped_command.startswith("'"):
            closing_quote_index = (
                stripped_command.find("'", 1)
            )

            if closing_quote_index == -1:
                return ""

            executable_path = stripped_command[
                1:closing_quote_index
            ]
        else:
            executable_path = (
                stripped_command.split(maxsplit=1)[0]
            )

        return os.path.basename(
            executable_path
        )

    @staticmethod
    def _format_result(
        result: CommandResult,
    ) -> str:
        """
        把 CommandResult 格式化为字符串，
        方便作为工具结果返回给大模型。
        """
        if result.timed_out:
            status_text = "执行超时"
        elif result.exit_code == 0:
            status_text = "执行成功"
        else:
            status_text = "执行失败"

        exit_code_text = (
            str(result.exit_code)
            if result.exit_code is not None
            else "无"
        )

        return (
            f"命令：{result.command}\n"
            f"执行状态：{status_text}\n"
            f"退出码：{exit_code_text}\n\n"
            f"stdout:\n"
            f"{result.stdout or '(无输出)'}\n\n"
            f"stderr:\n"
            f"{result.stderr or '(无输出)'}"
        )

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": (
                                "需要在工作区根目录中执行的命令，"
                                "例如 python -m pytest、git status"
                            ),
                        },
                        "timeout": {
                            "type": "integer",
                            "description": (
                                "命令执行超时时间，单位为秒；"
                                "默认 60 秒，最大 600 秒"
                            ),
                        },
                    },
                    "required": ["command"],
                    "additionalProperties": False,
                },
            },
        }