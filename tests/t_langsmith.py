from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()


@traceable(name="add_numbers")
def add_numbers(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    result = add_numbers(10, 20)
    print(result)