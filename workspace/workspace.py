from pathlib import Path

class Workspace:
    """
    管理 SWE Agent 可以操作的代码工作区。
    Agent 后续读取文件、修改文件、搜索代码、执行命令，
    都必须以这个工作区为根目录。
    """
    def __init__(self,root_path:str):
        """
        初始化工作区
        root_path 被agent操作的项目目录
        """
        self.root = Path(root_path).resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"工作区不存在：{self.root}")
        if not self.root.is_dir():
            raise NotADirectoryError(f"工作区不是目录：{self.root}")

    def resolve_path(self,relative_path:str) -> Path:
        """
        相对路径 -》 绝对路径
        :param relative_path:相对路径
        :return:
        """
        target_path = (self.root / relative_path).resolve()  # 使用 / 运算符拼接路径（pathlib 的特性）
        try:
            # 检查 target_path 是否位于 self.root 下面
            target_path.relative_to(self.root)
        except ValueError as exc:
            raise PermissionError(f"禁止访问工作区之外的路径：{relative_path}") from exc
        return target_path