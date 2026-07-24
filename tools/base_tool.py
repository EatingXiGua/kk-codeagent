from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    """
    所有工具的抽象基类
    后续的文件读取工具、文件写入工具、代码搜索工具等都需要继承BaseTool
    """
    # 工具名称
    name: str
    # 工具功能描述：大模型会通过这个描述了解工具的作用
    description: str

    @abstractmethod
    def execute(self,**kwargs:Any) -> str:
        """
        执行工具的具体功能
        不同的工具会接收不同参数，因此这里用**kwargs
        :param kwargs:
        :return: 工具执行后的字符串结果
        """
        pass

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """
        返回工具的schema
        schema用于告诉大模型：工具叫什么名字、工具有哪些作用、工具有哪些参数、哪些参数是必填的
        :return: 符合大模型调用格式的字典
        """
        pass
