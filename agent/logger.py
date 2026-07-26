from typing import Any


class AgentLogger:
    """
    Agent 运行日志。

    第一版直接打印到终端。
    后续可以扩展为写入日志文件。
    """

    def log_step(self, step: int) -> None:
        print(f"\n========== 第 {step} 轮 ==========")

    def log_model_content(
        self,
        content: str | None,
    ) -> None:
        if content:
            print("\n模型回复：")
            print(content)

    def log_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> None:
        print("\n模型请求调用工具：")
        print(f"工具名称：{tool_name}")
        print(f"工具参数：{arguments}")

    def log_tool_result(
        self,
        tool_name: str,
        result: str,
    ) -> None:
        print(f"\n工具 {tool_name} 执行结果：")
        print(result)

    def log_finished(self, final_answer: str) -> None:
        print("\n========== Agent 执行完成 ==========")
        print(final_answer)

    def log_max_steps(self, max_steps: int) -> None:
        print(
            f"\nAgent 已达到最大执行轮数：{max_steps}"
        )