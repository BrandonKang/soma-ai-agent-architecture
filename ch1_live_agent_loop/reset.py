"""sample_repo/src/auth/login.py를 실습 시작 전(버그 있는) 상태로 되돌린다.

실제 Claude Code가 이 파일을 직접 수정하기 때문에, 다시 처음부터 실습하려면
이 스크립트를 먼저 실행한다.
실행: python3 reset.py
"""
from pathlib import Path

LOGIN_PY = Path(__file__).parent / "sample_repo" / "src" / "auth" / "login.py"

ORIGINAL = '''"""로그인 처리 모듈 (실습용으로 일부러 버그를 심어둠)"""


def is_token_expired(now: float, expires_at: float) -> bool:
    """현재 시각이 만료 시각을 지났으면 True를 반환해야 한다."""
    return now < expires_at


def login(now: float, expires_at: float) -> str:
    if is_token_expired(now, expires_at):
        return "로그인 실패: 세션이 만료되었습니다"
    return "로그인 성공"
'''

if __name__ == "__main__":
    LOGIN_PY.write_text(ORIGINAL)
    print(f"초기화 완료: {LOGIN_PY} 를 버그 있는 상태로 되돌렸습니다.")
