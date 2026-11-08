"""sample_repo를 실습 시작 전 상태로 되돌린다.

- src/utils/formatting.py 를 원본으로 복원 (추가된 함수 제거)
- src/utils/currency.py 가 있으면 삭제 (CLAUDE.md 적용 후 생성되는 파일)
- CLAUDE.md 가 있으면 삭제 (다시 "지침 없는 상태"부터 실습하기 위해)
- __pycache__ 정리

실행: python3 reset.py
"""
from pathlib import Path

REPO = Path(__file__).parent / "sample_repo"
FORMATTING_PY = REPO / "src" / "utils" / "formatting.py"
CURRENCY_PY = REPO / "src" / "utils" / "currency.py"
CLAUDE_MD = REPO / "CLAUDE.md"

ORIGINAL_FORMATTING = '''"""화면 표시용 포맷팅 유틸리티 모음"""


def format_date(year: int, month: int, day: int) -> str:
    """YYYY-MM-DD 형식의 날짜 문자열을 반환한다."""
    return f"{year:04d}-{month:02d}-{day:02d}"


def format_percentage(ratio: float) -> str:
    """0~1 사이의 비율을 '42%' 같은 문자열로 반환한다."""
    return f"{round(ratio * 100)}%"
'''

if __name__ == "__main__":
    FORMATTING_PY.write_text(ORIGINAL_FORMATTING)
    print(f"복원 완료: {FORMATTING_PY}")

    if CURRENCY_PY.exists():
        CURRENCY_PY.unlink()
        print(f"삭제 완료: {CURRENCY_PY}")

    if CLAUDE_MD.exists():
        CLAUDE_MD.unlink()
        print(f"삭제 완료: {CLAUDE_MD}")

    for pycache in REPO.rglob("__pycache__"):
        for f in pycache.glob("*"):
            f.unlink()
        pycache.rmdir()

    print("초기화 완료.")
