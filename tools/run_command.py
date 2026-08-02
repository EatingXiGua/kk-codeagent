import os
import re
from typing import ClassVar

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from sandbox import CommandExecutor, CommandResult
from workspace.workspace import Workspace


class RunCommandInput(BaseModel):
    command: str = Field(
        min_length=1,
        description="Allowed command to run in the workspace root.",
    )
    timeout: int | None = Field(
        default=None,
        description="Optional command timeout in seconds.",
    )


class RunCommandTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "run_command"
    description: str = "Run an allowed command in the workspace root."
    args_schema: type[BaseModel] = RunCommandInput

    workspace: Workspace
    default_timeout: int = 60
    max_output_length: int = 20_000

    _executor: CommandExecutor = PrivateAttr()

    allowed_executables: ClassVar[set[str]] = {
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

    dangerous_patterns: ClassVar[list[str]] = [
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

    def model_post_init(self, __context: object) -> None:
        self._executor = CommandExecutor(
            working_directory=self.workspace.root,
            default_timeout=self.default_timeout,
            max_output_length=self.max_output_length,
        )

    def _run(
        self,
        command: str,
        timeout: int | None = None,
    ) -> str:
        command = command.strip()

        validation_error = self._validate_command(command)

        if validation_error:
            return validation_error

        if timeout is not None:
            if timeout <= 0:
                return "Invalid arguments: timeout must be greater than 0"

            if timeout > 600:
                return "Invalid arguments: timeout cannot exceed 600 seconds"

        result = self._executor.execute(
            command=command,
            timeout=timeout,
        )

        return self._format_result(result)

    def _validate_command(
        self,
        command: str,
    ) -> str | None:
        for pattern in self.dangerous_patterns:
            if re.search(
                pattern,
                command,
                flags=re.IGNORECASE,
            ):
                return (
                    "Command rejected: detected a dangerous or disallowed "
                    "operation."
                )

        forbidden_separators = {
            "&&",
            "||",
            ";",
            "\n",
            "\r",
        }

        if any(separator in command for separator in forbidden_separators):
            return (
                "Command rejected: command chaining and multi-line commands "
                "are not allowed."
            )

        executable = self._extract_executable(command)

        if not executable:
            return "Command rejected: executable cannot be identified."

        allowed = {
            item.lower()
            for item in self.allowed_executables
        }

        if executable.lower() not in allowed:
            return (
                f"Command rejected: executable is not allowed: {executable}\n"
                "Allowed executables: "
                + ", ".join(sorted(self.allowed_executables))
            )

        return None

    @staticmethod
    def _extract_executable(command: str) -> str:
        stripped_command = command.strip()

        if stripped_command.startswith('"'):
            closing_quote_index = stripped_command.find('"', 1)

            if closing_quote_index == -1:
                return ""

            executable_path = stripped_command[1:closing_quote_index]
        elif stripped_command.startswith("'"):
            closing_quote_index = stripped_command.find("'", 1)

            if closing_quote_index == -1:
                return ""

            executable_path = stripped_command[1:closing_quote_index]
        else:
            executable_path = stripped_command.split(maxsplit=1)[0]

        return os.path.basename(executable_path)

    @staticmethod
    def _format_result(result: CommandResult) -> str:
        if result.timed_out:
            status_text = "timed out"
        elif result.exit_code == 0:
            status_text = "succeeded"
        else:
            status_text = "failed"

        exit_code_text = (
            str(result.exit_code)
            if result.exit_code is not None
            else "none"
        )

        return (
            f"Command: {result.command}\n"
            f"Status: {status_text}\n"
            f"Exit code: {exit_code_text}\n\n"
            f"stdout:\n"
            f"{result.stdout or '(no output)'}\n\n"
            f"stderr:\n"
            f"{result.stderr or '(no output)'}"
        )
