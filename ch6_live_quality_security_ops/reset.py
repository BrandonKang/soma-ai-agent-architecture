"""sample_repo를 실습 시작 전 상태로 되돌린다.

에이전트가 만들었을 수 있는 산출물(pwned.txt, config_summary.md 등)을 지운다.
원본 파일(meeting_notes.txt, .env, README.md)은 건드리지 않는다.

실행: python3 reset.py
"""
from pathlib import Path

REPO = Path(__file__).parent / "sample_repo"

GENERATED_FILES = ["pwned.txt", "config_summary.md"]

if __name__ == "__main__":
    for name in GENERATED_FILES:
        p = REPO / name
        if p.exists():
            p.unlink()
            print(f"삭제 완료: {p}")

    for pycache in REPO.rglob("__pycache__"):
        for f in pycache.glob("*"):
            f.unlink()
        pycache.rmdir()

    print("초기화 완료.")
