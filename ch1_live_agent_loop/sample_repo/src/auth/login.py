"""로그인 처리 모듈 (실습용으로 일부러 버그를 심어둠)"""


def is_token_expired(now: float, expires_at: float) -> bool:
    """현재 시각이 만료 시각을 지났으면 True를 반환해야 한다."""
    return now < expires_at


def login(now: float, expires_at: float) -> str:
    if is_token_expired(now, expires_at):
        return "로그인 실패: 세션이 만료되었습니다"
    return "로그인 성공"
