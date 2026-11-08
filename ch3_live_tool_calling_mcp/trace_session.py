"""방금 진행한 실제 Claude Code 세션의 내부 메시지 흐름 + 컨텍스트 크기를 보여준다.

1장의 trace_session.py와 같은 원리다. 2장에서는 추가로 각 턴마다
"지금 모델에게 들어간 컨텍스트가 얼마나 쌓였는지"를 토큰 수로 같이 보여준다.
(cache_read_input_tokens + cache_creation_input_tokens = 그 호출 시점의
입력 컨텍스트 크기. 턴이 지날수록 이 값이 커지는 걸 직접 확인하는 게 목적이다.)

사용법 (claude를 실행했던 폴더, 즉 sample_repo 안에서):
    python3 ../trace_session.py                # 가장 최근 세션
    python3 ../trace_session.py --list         # 이 폴더의 세션 목록 보기
    python3 ../trace_session.py <세션id 일부>   # 특정 세션 지정
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


def context_size(message: dict) -> int | None:
    usage = message.get("usage")
    if not usage:
        return None
    return usage.get("cache_read_input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)


def print_trace(jsonl_path: Path) -> None:
    print(f"# 세션 파일: {jsonl_path}\n")
    turn = 0
    pending: list[tuple[str, object]] = []
    pending_ctx: int | None = None

    def flush_turn() -> None:
        nonlocal turn, pending, pending_ctx
        if not pending:
            return
        turn += 1
        ctx_note = f"  [이 시점 컨텍스트 ≈ {pending_ctx:,} 토큰]" if pending_ctx is not None else ""
        print(f"[턴 {turn}] 모델 호출 1회{ctx_note}")
        for btype, payload in pending:
            if btype == "tool_use":
                name, tool_input = payload
                print(f"        -> 도구 호출: {name}({short(tool_input)})")
            else:
                print(f"        -> 텍스트: {short(payload, 160)}")
        pending = []
        pending_ctx = None

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

            # assistant
            size = context_size(message)
            if size is not None:
                pending_ctx = size  # 같은 턴 안에서는 마지막 값으로 덮어써도 충분하다

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

    flush_turn()


def main() -> None:
    cwd = Path.cwd()
    log_dir = project_log_dir(cwd)
    sessions = list_sessions(log_dir)

    if not sessions:
        print(f"세션 파일을 찾지 못했습니다: {log_dir}")
        print("claude를 이 폴더(보통 sample_repo)에서 먼저 실행한 뒤 다시 시도하라.")
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
        target = sessions[-1]

    print_trace(target)


if __name__ == "__main__":
    main()
