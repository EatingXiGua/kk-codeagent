import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CommandResult:
    """
    命令执行结果。

    将 subprocess 返回的信息封装成统一对象，
    避免 RunCommandTool 直接依赖 subprocess.CompletedProcess。
    """

    # 原始命令
    command: str

    # 命令退出码
    # 0 一般表示成功，非 0 一般表示执行失败
    # 超时时没有正常退出码，所以为 None
    exit_code: int | None

    # 标准输出
    stdout: str

    # 标准错误输出
    stderr: str

    # 是否执行超时
    timed_out: bool = False


class CommandExecutor:
    """
    本地命令执行器。

    负责：
    1. 在指定工作目录执行命令
    2. 限制命令执行时间
    3. 收集 stdout 和 stderr
    4. 限制返回给 Agent 的输出长度

    注意：
    这只是基础的本地执行器，不是真正安全的系统沙箱。
    """

    def __init__(
        self,
        working_directory: Path,
        default_timeout: int = 60,
        max_output_length: int = 20_000,
    ):
        """
        初始化命令执行器。

        :param working_directory:
            命令执行时使用的工作目录

        :param default_timeout:
            默认超时时间，单位为秒

        :param max_output_length:
            stdout 和 stderr 最多保留多少个字符
        """
        self.working_directory = working_directory.resolve()
        self.default_timeout = default_timeout
        self.max_output_length = max_output_length

        if not self.working_directory.exists():
            raise FileNotFoundError(
                f"命令工作目录不存在：{self.working_directory}"
            )

        if not self.working_directory.is_dir():
            raise NotADirectoryError(
                f"命令工作路径不是目录：{self.working_directory}"
            )

        if self.default_timeout <= 0:
            raise ValueError(
                "default_timeout 必须大于 0"
            )

        if self.max_output_length <= 0:
            raise ValueError(
                "max_output_length 必须大于 0"
            )

    def execute(
        self,
        command: str,
        timeout: int | None = None,
    ) -> CommandResult:
        """
        执行命令。

        :param command:
            要执行的命令，例如：
            python -m pytest
            git status

        :param timeout:
            本次命令的超时时间。
            不传时使用 default_timeout。

        :return:
            CommandResult
        """
        if not command or not command.strip():
            raise ValueError(
                "command 不能为空"
            )

        actual_timeout = (
            timeout
            if timeout is not None
            else self.default_timeout
        )

        if actual_timeout <= 0:
            raise ValueError(
                "timeout 必须大于 0"
            )

        try:
            completed_process = subprocess.run(
                command,
                cwd=self.working_directory,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=actual_timeout,
            )

            return CommandResult(
                command=command,
                exit_code=completed_process.returncode,
                stdout=self._truncate_output(
                    completed_process.stdout
                ),
                stderr=self._truncate_output(
                    completed_process.stderr
                ),
                timed_out=False,
            )

        except subprocess.TimeoutExpired as exc:
            stdout = self._convert_timeout_output(
                exc.stdout
            )
            stderr = self._convert_timeout_output(
                exc.stderr
            )

            return CommandResult(
                command=command,
                exit_code=None,
                stdout=self._truncate_output(stdout),
                stderr=self._truncate_output(stderr),
                timed_out=True,
            )

        except OSError as exc:
            return CommandResult(
                command=command,
                exit_code=None,
                stdout="",
                stderr=(
                    f"{type(exc).__name__}: {exc}"
                ),
                timed_out=False,
            )

    def _truncate_output(
        self,
        output: str | None,
    ) -> str:
        """
        截断过长输出。

        这里保留输出末尾，因为编译错误和测试错误
        通常出现在输出的最后部分。
        """
        if not output:
            return ""

        if len(output) <= self.max_output_length:
            return output

        omitted_length = (
            len(output) - self.max_output_length
        )

        return (
            f"...前面省略了 {omitted_length} 个字符...\n"
            + output[-self.max_output_length:]
        )

    @staticmethod
    def _convert_timeout_output(
        output: str | bytes | None,
    ) -> str:
        """
        subprocess 超时时，stdout 和 stderr
        有时可能是 bytes，因此统一转成字符串。
        """
        if output is None:
            return ""

        if isinstance(output, bytes):
            return output.decode(
                "utf-8",
                errors="replace",
            )

        return output