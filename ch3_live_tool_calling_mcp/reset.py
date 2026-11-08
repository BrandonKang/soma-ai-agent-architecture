"""sample_repo를 실습 시작 전 상태로 되돌린다.

- sample_repo/.claude/settings.json 삭제 (권한 규칙 초기화)
- toy-dice MCP 서버 등록 해제 (claude mcp remove)
- __pycache__ 정리

실행: python3 reset.py
"""
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).parent / "sample_repo"
SETTINGS = REPO / ".claude" / "settings.json"

if __name__ == "__main__":
    if SETTINGS.exists():
        SETTINGS.unlink()
        print(f"삭제 완료: {SETTINGS}")
        claude_dir = SETTINGS.parent
        if claude_dir.exists() and not any(claude_dir.iterdir()):
            claude_dir.rmdir()

    result = subprocess.run(
        ["claude", "mcp", "remove", "toy-dice", "-s", "local"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("MCP 서버 toy-dice 등록 해제 완료")
    else:
        print("MCP 서버 toy-dice: 등록되어 있지 않거나 이미 해제됨 (무시해도 됨)")

    for pycache in REPO.rglob("__pycache__"):
        shutil.rmtree(pycache)

    print("초기화 완료.")
