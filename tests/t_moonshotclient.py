from llm import MoonshotLLMClient


def main():
    client = MoonshotLLMClient()

    response = client.chat(
        messages=[
            {
                "role": "system",
                "content": "你是一个简洁的编程助手。",
            },
            {
                "role": "user",
                "content": "用一句话解释什么是 Python。",
            },
        ]
    )

    print("模型名称：")
    print(client.model)

    print("\n模型回答：")
    print(response.content)

    print("\n是否请求调用工具：")
    print(response.has_tool_calls)


if __name__ == "__main__":
    main()