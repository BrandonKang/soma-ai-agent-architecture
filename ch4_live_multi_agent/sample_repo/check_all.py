"""mod_a, mod_b, mod_c가 전부 고쳐졌는지 한 번에 확인한다.

실행: python3 check_all.py
"""
import sys

from mod_a import add
from mod_b import greet
from mod_c import is_even


def run() -> int:
    checks = [
        ("mod_a.add(2, 3) == 5", add(2, 3), 5),
        ("mod_b.greet('claude') == 'Hello, Claude!'", greet("claude"), "Hello, Claude!"),
        ("mod_c.is_even(4) == True", is_even(4), True),
        ("mod_c.is_even(3) == False", is_even(3), False),
    ]

    failed = 0
    for name, actual, expected in checks:
        ok = actual == expected
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"[{status}] {name} -> actual={actual!r}")

    if failed:
        print(f"\n{failed}건 실패")
        return 1

    print("\n전체 통과")
    return 0


if __name__ == "__main__":
    sys.exit(run())
