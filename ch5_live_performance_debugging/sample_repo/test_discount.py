import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from discount import apply_discount  # noqa: E402


def run():
    # 10000원의 20% 할인은 8000원이어야 하는데, 아래 기대값은 7000으로 잘못 적혀 있다
    result = apply_discount(10000, 0.2)
    assert result == 7000, f"기대값 7000, 실제 {result}"
    print("전체 통과")


if __name__ == "__main__":
    run()
