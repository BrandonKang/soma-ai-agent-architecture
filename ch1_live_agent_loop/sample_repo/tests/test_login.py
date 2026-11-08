"""pytest 없이 단독 실행 가능한 테스트 스크립트.

실행: python3 sample_repo/tests/test_login.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "auth"))

from login import login  # noqa: E402


def run() -> int:
    checks = [
        ("만료된 토큰이면 로그인 실패해야 한다", login(100, 50), "로그인 실패: 세션이 만료되었습니다"),
        ("아직 유효한 토큰이면 로그인 성공해야 한다", login(10, 50), "로그인 성공"),
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
