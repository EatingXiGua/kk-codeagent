from pathlib import Path

import pytest

from workspace.workspace import Workspace


def test_create_workspace(tmp_path: Path):
    """
    测试能够正常创建工作区。
    """
    workspace = Workspace(str(tmp_path))

    assert workspace.root == tmp_path.resolve()


def test_resolve_valid_path(tmp_path: Path):
    """
    测试解析工作区内部路径。
    """
    workspace = Workspace(str(tmp_path))

    result = workspace.resolve_path("src/main.py")

    expected = (tmp_path / "src/main.py").resolve()

    assert result == expected


def test_block_outside_path(tmp_path: Path):
    """
    测试禁止访问工作区外部。
    """
    workspace = Workspace(str(tmp_path))

    with pytest.raises(PermissionError):
        workspace.resolve_path("../secret.txt")


def test_workspace_not_exists(tmp_path: Path):
    """
    测试工作区不存在时抛出异常。
    """
    nonexistent_path = tmp_path / "not_exists"

    with pytest.raises(FileNotFoundError):
        Workspace(str(nonexistent_path))


def test_workspace_is_file(tmp_path: Path):
    """
    测试传入文件而不是目录时抛出异常。
    """
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        Workspace(str(file_path))