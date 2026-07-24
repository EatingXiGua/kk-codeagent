import os
import re
import subprocess # 创建子进程执行外部命令
from typing import Any

from tools.base_tool import BaseTool
from workspace.workspace import Workspace


class RunCommandTool(BaseTool):
    """
    在工作区目录中运行命令。
    """

    name = "run_command"
    description = "在工作区根目录中执行测试、编译或代码检查命令"

    ALLOWED_EXECUTABLES = {
        "python",
        "python3",
        "pytest",
        "pip",
        "pip3",
        "git",
        "mvn",
        "mvnw",
        "mvnw.cmd",
        "gradle",
        "gradlew",
        "gradlew.bat",
        "npm",
        "npm.cmd",
        "npx",
        "npx.cmd",
        "node",
        "ruff",
        "black",
        "mypy",
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
        self.default_timeout = default_timeout
        self.max_output_length = max_output_length

    def execute(
        self,
        command: str,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        在工作区内执行命令。

        :param command: 要执行的命令
        :param timeout: 超时时间，单位为秒
        """
        if not command or not command.strip():
            return "参数错误：command 不能为空"

        command = command.strip()

        # 安全检查，有错误则返回
        validation_error = self._validate_command(command)
        if validation_error:
            return validation_error

        # 确定超时时间
        actual_timeout = (
            timeout
            if timeout is not None
            else self.default_timeout
        )

        if actual_timeout <= 0:
            return "参数错误：timeout 必须大于 0"

        if actual_timeout > 600:
            return "参数错误：timeout 不能超过 600 秒"

        try:
            result = subprocess.run( # subprocess.run执行命令
                command, # 命令
                cwd=self.workspace.root, # 根目录
                shell=True, # 通过shell执行
                capture_output=True, # 捕获stdout和stderr
                text=True, # 返回字符串
                encoding="utf-8",
                errors="replace",
                timeout=actual_timeout,
            )

            stdout = self._truncate_output(result.stdout) # 调用_truncate_output截断过长的输出
            stderr = self._truncate_output(result.stderr)

            return (
                f"命令：{command}\n"
                f"工作目录：{self.workspace.root}\n"
                f"退出码：{result.returncode}\n\n"
                f"stdout:\n"
                f"{stdout or '(无输出)'}\n\n"
                f"stderr:\n"
                f"{stderr or '(无输出)'}"
            )

        except subprocess.TimeoutExpired as exc: # 超时异常 当命令执行时间超过timeout时抛出
            stdout = self._convert_timeout_output(exc.stdout) # _convert_timeout_output将输出转化为字符串
            stderr = self._convert_timeout_output(exc.stderr)

            return (
                f"命令执行超时：{command}\n"
                f"超时时间：{actual_timeout} 秒\n\n"
                f"stdout:\n"
                f"{self._truncate_output(stdout) or '(无输出)'}\n\n"
                f"stderr:\n"
                f"{self._truncate_output(stderr) or '(无输出)'}"
            )

        except OSError as exc: # 系统错误
            return (
                f"命令执行失败：{command}\n"
                f"错误类型：{type(exc).__name__}\n"
                f"错误信息：{exc}"
            )

    def _validate_command(self, command: str) -> str | None:
        """
        对命令进行基础安全检查。
        """
        lowered_command = command.lower()

        # 遍历所有的危险模式，如果匹配到任何一个，就拒绝执行
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(
                pattern,
                lowered_command,
                flags=re.IGNORECASE,
            ):
                return (
                    "命令被拒绝：检测到危险命令或不允许的操作"
                )

        # 第一版不允许一次执行多个命令
        dangerous_separators = [
            "&&",
            "||",
            ";",
            "\n",
            "\r",
        ]

        if any(
            separator in command
            for separator in dangerous_separators
        ):
            return (
                "命令被拒绝：第一版暂不允许使用 "
                "&&、||、分号或多行命令"
            )

        # 提取可执行程序的名称
        executable = self._extract_executable(command)

        if not executable:
            return "命令被拒绝：无法识别可执行程序"
        # 检查是否在白名单中 不在则拒绝执行
        if executable.lower() not in self.ALLOWED_EXECUTABLES:
            return (
                f"命令被拒绝：不允许执行 {executable}\n"
                "允许的程序包括："
                + ", ".join(sorted(self.ALLOWED_EXECUTABLES))
            )

        return None

    @staticmethod
    def _extract_executable(command: str) -> str:
        """
        提取命令中的第一个程序名称。

        例如：
        python -m pytest  -> python
        git status        -> git
        """
        first_part = command.strip().split(maxsplit=1)[0]

        # 处理被双引号包裹的简单情况
        first_part = first_part.strip("\"'")

        return os.path.basename(first_part)

    def _truncate_output(self, output: str | None) -> str:
        """
        限制命令输出长度，避免一次发送给模型过多内容。

        保留输出末尾，因为报错通常出现在最后。
        """
        if not output:
            return ""

        if len(output) <= self.max_output_length:
            return output

        omitted_length = len(output) - self.max_output_length

        return (
            f"...前面省略了 {omitted_length} 个字符...\n"
            + output[-self.max_output_length:]
        )

    @staticmethod
    def _convert_timeout_output(
        output: str | bytes | None,
    ) -> str:
        if output is None:
            return ""

        if isinstance(output, bytes):
            return output.decode(
                "utf-8",
                errors="replace",
            )

        return output

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
                                "需要在工作区根目录执行的命令，"
                                "例如 python -m pytest 或 git diff"
                            ),
                        },
                        "timeout": {
                            "type": "integer",
                            "description": (
                                "命令执行超时时间，单位为秒，"
                                "默认 60 秒，最大 600 秒"
                            ),
                        },
                    },
                    "required": ["command"],
                    "additionalProperties": False,
                },
            },
        }