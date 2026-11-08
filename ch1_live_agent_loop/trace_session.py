"""방금 진행한 실제 Claude Code 세션의 내부 메시지 흐름을 사람이 읽기 쉽게 보여준다.

Claude Code는 세션마다 ~/.claude/projects/<작업폴더경로>/<세션id>.jsonl 에
그 세션의 전체 messages(대화 이력)를 그대로 기록한다. 1장 슬라이드의

    messages = [system_prompt, user_request]
    while True:
        response = llm(messages, tools)
        ...

가 추상적인 설명이 아니라, 실제로 디스크에 저장되는 파일이라는 것을 직접 확인하기 위한
도구다. 이 스크립트는 그 파일을 파싱해서 슬라이드 8페이지와 같은 턴 표를 자동으로 만든다.

사용법 (sample_repo가 아니라 claude를 실행했던 폴더에서):
    python3 trace_session.py                # 가장 최근 세션
    python3 trace_session.py --list         # 이 폴더의 세션 목록 보기
    python3 trace_session.py <세션id 일부>   # 특정 세션 지정
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def project_log_dir(cwd: Path) -> Path:
    # Claude Code는 작업 폴더 경로의 "/"와 "_"를 모두 "-"로 바꿔 폴더명을 만든다.
    slug = str(cwd.resolve()).replace("/", "-").replace("_", "-")
    return Path.home() / ".claude" / "projects" / slug


def list_sessions(log_dir: Path) -> list[Path]:
    if not log_dir.exists():
        return []
    return sorted(log_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)


def short(value, limit: int = 90) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = text.replace("\n", " ⏎ ")
    return text if len(text) <= limit else text[:limit] + " ...(생략)"


def print_trace(jsonl_path: Path) -> None:
    """슬라이드 7페이지 의사코드의 한 바퀴(while 루프 1회 = 모델 호출 1번)를
    '턴' 하나로 묶어서 보여준다.

    주의: Claude Code는 모델 응답 하나(텍스트+도구 호출 등 여러 블록을 포함할 수 있다)를
    내부적으로 블록 단위 여러 줄의 JSONL 레코드로 나눠 기록한다. 그래서 단순히
    JSONL 줄 하나 = 턴 하나로 세면 안 되고, "다음 user 레코드(=도구 결과 또는 사람의
    새 입력)가 나오기 전까지 연속된 assistant 레코드들"을 모아야 실제 모델 호출 1번과
    일치한다.
    """
    print(f"# 세션 파일: {jsonl_path}\n")
    turn = 0
    pending: list[tuple[str, object]] = []  # 현재 턴에 쌓이는 (블록타입, 내용)

    def flush_turn() -> None:
        nonlocal turn, pending
        if not pending:
            return
        turn += 1
        print(f"[턴 {turn}] 모델 호출 1회 (response = llm(messages, tools))")
        for btype, payload in pending:
            if btype == "tool_use":
                name, tool_input = payload
                print(f"        -> 도구 호출: {name}({short(tool_input)})")
            else:  # text
                print(f"        -> 텍스트: {short(payload, 160)}")
        pending = []

    with jsonl_path.open() as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            rec_type = record.get("type")
            if rec_type not in ("user", "assistant"):
                continue

            message = record.get("message", {})
            content = message.get("content")

            if rec_type == "user":
                # user 레코드가 나왔다는 건 직전까지 쌓인 assistant 블록들이
                # 모델의 '한 번의 호출' 전체였다는 뜻 -> 먼저 턴으로 마감한다.
                flush_turn()

                if isinstance(content, str):
                    if content.strip():
                        print(f"\n[사용자] {short(content, 200)}\n")
                    continue

                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            print(f"        <- 하네스가 실행한 결과: {short(block.get('content'))}")
                    print()
                continue

            # rec_type == "assistant": 블록들을 현재 턴에 쌓기만 하고, 아직 출력하지 않는다.
            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")

                if btype == "tool_use":
                    pending.append(("tool_use", (block.get("name"), block.get("input"))))

                elif btype == "text":
                    text = block.get("text", "").strip()
                    if text:
                        pending.append(("text", text))

                # "thinking" 블록은 슬라이드 범위를 벗어나므로 표시하지 않는다.

    flush_turn()  # 파일 끝에 남아있는 마지막 턴(보통 최종 답변) 처리


def main() -> None:
    cwd = Path.cwd()
    log_dir = project_log_dir(cwd)
    sessions = list_sessions(log_dir)

    if not sessions:
        print(f"세션 파일을 찾지 못했습니다: {log_dir}")
        print("claude를 이 폴더에서 먼저 실행한 뒤 다시 시도하라.")
        sys.exit(1)

    args = sys.argv[1:]

    if args and args[0] == "--list":
        for p in sessions:
            print(p.stem, "-", p)
        return

    if args:
        matches = [p for p in sessions if args[0] in p.stem]
        if not matches:
            print(f"'{args[0]}'을 포함하는 세션을 찾지 못했습니다. --list로 목록을 확인하라.")
            sys.exit(1)
        target = matches[-1]
    else:
        target = sessions[-1]  # 가장 최근 세션

    print_trace(target)


if __name__ == "__main__":
    main()
