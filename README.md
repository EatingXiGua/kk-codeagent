# SWE Agent

这是一个基于 Python、LangChain、LangGraph 和 LangSmith 的简易 SWE Agent。

当前版本只保留 LangGraph 版 Agent 入口：模型通过 LangChain 调用 Moonshot/Kimi，工具通过 LangChain tools 暴露给 LangGraph，运行轨迹可接入 LangSmith 观察。

## 主要功能

- 使用 LangGraph 编排 Agent 循环
- 使用 LangChain `ChatOpenAI` 兼容接入 Moonshot/Kimi
- 使用 LangChain tools 包装本地工具能力
- 支持查看目录、读取文件、搜索代码、写入文件、运行白名单命令
- 使用 `Workspace` 限制文件访问范围
- 可选接入 LangSmith 记录运行轨迹

## 项目结构

```text
sweagent/
├── agent/              # LangGraph Agent 封装
├── graph/              # LangGraph 图构建
├── llm/                # LangChain Moonshot 模型适配
├── tools/              # 本地工具和 LangChain tools 适配
├── workspace/          # 工作区路径管理
├── sandbox/            # 本地命令执行封装
├── observability/      # LangSmith 接入
├── tests/              # 自动化测试和手工测试脚本
└── main.py             # 标准入口
```

## 环境变量

复制 `.env.example` 为 `.env`，然后填入本地真实配置：

```bash
MOONSHOT_API_KEY=your_moonshot_api_key
MOONSHOT_MODEL=kimi-k2.6
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1

LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=sweagent-v1
```

`.env` 会被 Git 忽略，不要把真实 API Key 提交到仓库。

## 安装依赖

```bash
pip install -r requirements.txt
```

如果使用本项目的 conda 环境：

```bash
D:\AppDir\miniconda311\envs\swe-agent\python.exe -m pip install -r requirements.txt
```

## 运行

```bash
python main.py 查看当前项目结构，并说明主要模块
```

也可以指定最大图执行步数：

```bash
python main.py --max-steps 20 查看当前项目结构
```

检查 LangSmith 配置：

```bash
python main.py --langsmith-status
```

## 测试

```bash
python -m pytest
```

当前测试不依赖真实模型网络调用，主要覆盖工作区路径保护、命令执行、LangChain tools、Moonshot 模型工厂和 LangGraph 图构建。
