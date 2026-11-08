"""sample_repo를 실습 시작 전 상태로 되돌린다.

실행: python3 reset.py
"""
from pathlib import Path

REPO = Path(__file__).parent / "sample_repo"

DISCOUNT_PY = '''def apply_discount(price, rate):
    """price에서 rate(0~1) 비율만큼 할인한 금액을 반환한다."""
    return price - (price * rate)
'''

TEST_DISCOUNT_PY = '''import os
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
'''

if __name__ == "__main__":
    (REPO / "discount.py").write_text(DISCOUNT_PY)
    (REPO / "test_discount.py").write_text(TEST_DISCOUNT_PY)
    print(f"복원 완료: {REPO}")

    for pycache in REPO.rglob("__pycache__"):
        for f in pycache.glob("*"):
            f.unlink()
        pycache.rmdir()

    print("초기화 완료.")
