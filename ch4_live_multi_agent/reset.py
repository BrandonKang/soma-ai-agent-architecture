"""sample_repo의 세 버그 파일을 실습 시작 전 상태로 되돌린다.

실행: python3 reset.py
"""
from pathlib import Path

REPO = Path(__file__).parent / "sample_repo"

ORIGINALS = {
    "mod_a.py": '''def add(a, b):
    return a - b  # BUG: 덧셈이어야 하는데 뺄셈으로 되어 있다
''',
    "mod_b.py": '''def greet(name):
    return "hello " + name.upper()  # BUG: "Hello, 이름!" 형태로 인사해야 한다
''',
    "mod_c.py": '''def is_even(n):
    return n % 2 == 1  # BUG: 짝수 판별인데 홀수일 때 True를 반환한다
''',
}

if __name__ == "__main__":
    for filename, content in ORIGINALS.items():
        (REPO / filename).write_text(content)
        print(f"복원 완료: {REPO / filename}")

    for pycache in REPO.rglob("__pycache__"):
        for f in pycache.glob("*"):
            f.unlink()
        pycache.rmdir()

    print("초기화 완료.")
