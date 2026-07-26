import sys
from pathlib import Path

import pytest

from sandbox import CommandExecutor


def test_execute_successful_command(
    tmp_path: Path,
):
    executor = CommandExecutor(
        working_directory=tmp_path
    )

    command = (
        f'"{sys.executable}" '
        '-c "print(\'hello sandbox\')"'
    )

    result = executor.execute(command)

    assert result.exit_code == 0
    assert result.timed_out is False
    assert "hello sandbox" in result.stdout
    assert result.stderr == ""


def test_execute_failed_command(
    tmp_path: Path,
):
    executor = CommandExecutor(
        working_directory=tmp_path
    )

    command = (
        f'"{sys.executable}" '
        '-c "import sys; sys.exit(3)"'
    )

    result = executor.execute(command)

    assert result.exit_code == 3
    assert result.timed_out is False


def test_command_working_directory(
    tmp_path: Path,
):
    executor = CommandExecutor(
        working_directory=tmp_path
    )

    command = (
        f'"{sys.executable}" '
        '-c "import os; print(os.getcwd())"'
    )

    result = executor.execute(command)

    expected_path = str(tmp_path.resolve())

    assert result.exit_code == 0
    assert expected_path.lower() in result.stdout.lower()


def test_empty_command(
    tmp_path: Path,
):
    executor = CommandExecutor(
        working_directory=tmp_path
    )

    with pytest.raises(
        ValueError,
        match="command 不能为空",
    ):
        executor.execute("")


def test_invalid_working_directory(
    tmp_path: Path,
):
    nonexistent_path = (
        tmp_path / "not_exists"
    )

    with pytest.raises(
        FileNotFoundError,
    ):
        CommandExecutor(
            working_directory=nonexistent_path
        )


def test_output_truncation(
    tmp_path: Path,
):
    executor = CommandExecutor(
        working_directory=tmp_path,
        max_output_length=10,
    )

    command = (
        f'"{sys.executable}" '
        '-c "print(\'12345678901234567890\')"'
    )

    result = executor.execute(command)

    assert "前面省略了" in result.stdout
    assert result.stdout.endswith(
        "123456789\n"
    ) or len(result.stdout) > 10


def test_command_timeout(
    tmp_path: Path,
):
    executor = CommandExecutor(
        working_directory=tmp_path,
        default_timeout=1,
    )

    command = (
        f'"{sys.executable}" '
        '-c "import time; time.sleep(5)"'
    )

    result = executor.execute(command)

    assert result.timed_out is True
    assert result.exit_code is None