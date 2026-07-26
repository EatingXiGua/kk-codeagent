# SWE Agent
这是一个用 Python 实现的简单 SWE Agent 第一版本。

项目目标是让大模型具备基本的软件工程协作能力：理解用户任务，查看项目文件，搜索代码，修改文件，并运行测试或命令进行验证。当前版本重点实现了 Agent 主循环、工具调用机制、工作区路径限制，以及 Moonshot/Kimi 模型接入。
## 主要功能
- 基于大模型的任务执行循环
- 支持 OpenAI 兼容格式的工具调用
- 接入 Moonshot/Kimi API
- 工作区内文件读取、写入、搜索和目录查看
- 支持在工作区内运行白名单命令
- 对工具执行结果进行封装，并回传给模型继续推理
- 对工作区路径做基础保护，阻止访问工作区外文件

## Agent执行流程
SWEAgent 的核心流程如下：
1. 接收用户任务
2. 构造初始消息，包括系统提示词和用户任务
3. 调用大模型
4. 如果模型返回普通文本，则认为任务完成
5. 如果模型请求调用工具，则执行对应工具
6. 将工具执行结果加入消息历史
7. 再次调用模型，直到任务完成或达到最大轮数

## 已经实现工具
当前 Agent 支持以下工具：  
list_files	列出工作区内的文件和目录  
read_file	读取指定文本文件内容，并显示行号  
search_code	在工作区内搜索代码关键字  
write_file	创建或覆盖写入文件  
run_command	在工作区根目录执行测试、构建或检查命令  

## LLM配置
需要配置环境变量：  
MOONSHOT_API_KEY=你的 API Key  
可选环境变量配置：  
MOONSHOT_MODEL=kimi-k2.6  
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1  

## 运行例子
```
from agent import SWEAgent
from llm import MoonshotLLMClient
from tools import (
    ListFilesTool,
    ReadFileTool,
    RunCommandTool,
    SearchCodeTool,
    ToolManager,
    WriteFileTool,
)
from workspace.workspace import Workspace


workspace = Workspace("D:/pythonproject/sweagent")

tool_manager = ToolManager([
    ListFilesTool(workspace),
    ReadFileTool(workspace),
    SearchCodeTool(workspace),
    WriteFileTool(workspace),
    RunCommandTool(workspace),
])

llm_client = MoonshotLLMClient()

agent = SWEAgent(
    llm_client=llm_client,
    tool_manager=tool_manager,
    max_steps=10,
)

result = agent.run("查看当前项目结构，并说明主要模块")
print(result)
```
