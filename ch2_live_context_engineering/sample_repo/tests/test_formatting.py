"""pytest 없이 단독 실행 가능한 테스트 스크립트.

실행: python3 tests/test_formatting.py   (sample_repo 안에서)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "utils"))

from formatting import format_date, format_percentage  # noqa: E402


def run() -> int:
    checks = [
        ("날짜 포맷", format_date(2026, 1, 5), "2026-01-05"),
        ("퍼센트 포맷", format_percentage(0.4234), "42%"),
    ]

    failed = 0
    for name, actual, expected in checks:
        ok = actual == expected
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"[{status}] {name} -> actual={actual!r}, expected={expected!r}")

    if failed:
        print(f"\n{failed}건 실패")
        return 1

    print("\n전체 통과")
    return 0


if __name__ == "__main__":
    sys.exit(run())
