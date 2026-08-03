from pathlib import Path

import pytest

from workspace.workspace import Workspace


def test_create_workspace(tmp_path: Path):
    workspace = Workspace(tmp_path)

    assert workspace.root == tmp_path.resolve()


def test_resolve_valid_path(tmp_path: Path):
    workspace = Workspace(tmp_path)

    result = workspace.resolve_path("src/main.py")

    expected = (tmp_path / "src/main.py").resolve()

    assert result == expected


def test_block_outside_path(tmp_path: Path):
    workspace = Workspace(tmp_path)

    with pytest.raises(PermissionError):
        workspace.resolve_path("../secret.txt")


def test_resolve_file(tmp_path: Path):
    file_path = tmp_path / "main.py"
    file_path.write_text("print('hello')", encoding="utf-8")
    workspace = Workspace(tmp_path)

    assert workspace.resolve_file("main.py") == file_path.resolve()


def test_resolve_file_rejects_directory(tmp_path: Path):
    workspace = Workspace(tmp_path)

    with pytest.raises(IsADirectoryError):
        workspace.resolve_file(".")


def test_resolve_dir(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    workspace = Workspace(tmp_path)

    assert workspace.resolve_dir("src") == src_dir.resolve()


def test_resolve_dir_rejects_file(tmp_path: Path):
    file_path = tmp_path / "main.py"
    file_path.write_text("print('hello')", encoding="utf-8")
    workspace = Workspace(tmp_path)

    with pytest.raises(NotADirectoryError):
        workspace.resolve_dir("main.py")


def test_should_ignore_default_secret_files(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_local_file = tmp_path / ".env.local"
    env_file.write_text("secret", encoding="utf-8")
    env_local_file.write_text("secret", encoding="utf-8")
    workspace = Workspace(tmp_path)

    assert workspace.should_ignore(".env") is True
    assert workspace.should_ignore(".env.local") is True


def test_workspace_not_exists(tmp_path: Path):
    nonexistent_path = tmp_path / "not_exists"

    with pytest.raises(FileNotFoundError):
        Workspace(nonexistent_path)


def test_workspace_is_file(tmp_path: Path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        Workspace(file_path)
