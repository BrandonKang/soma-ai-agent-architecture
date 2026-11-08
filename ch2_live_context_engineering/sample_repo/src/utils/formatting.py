"""화면 표시용 포맷팅 유틸리티 모음"""


def format_date(year: int, month: int, day: int) -> str:
    """YYYY-MM-DD 형식의 날짜 문자열을 반환한다."""
    return f"{year:04d}-{month:02d}-{day:02d}"


def format_percentage(ratio: float) -> str:
    """0~1 사이의 비율을 '42%' 같은 문자열로 반환한다."""
    return f"{round(ratio * 100)}%"
