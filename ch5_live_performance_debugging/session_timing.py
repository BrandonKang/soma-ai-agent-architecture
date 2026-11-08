"""세션 하나의 "성능 영수증"을 뽑아준다.

슬라이드 5장의 공식을 실제 숫자로 채워 넣는 도구다.

    작업 시간 ≈ 모델 호출 횟수 × (입력 처리 + 출력 생성) + 도구 실행 시간

Claude Code는 세션이 끝날 때 "cost-state"라는 레코드에 그 세션 전체의
totalCostUSD(달러 비용, Claude Code가 공식적으로 계산한 값)·totalDuration(총
소요 시간, ms)·totalToolDuration(도구 실행에 쓴 시간, ms)을 남긴다. 여기에
각 턴의 timestamp를 더하면 턴 사이 지연 시간까지 볼 수 있다.

사용법 (claude를 실행했던 폴더에서):
    python3 ../session_timing.py
    python3 ../session_timing.py <세션id 일부>
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from trace_session import list_sessions, project_log_dir  # type: ignore


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def report(jsonl_path: Path) -> None:
    print(f"# 세션 파일: {jsonl_path}\n")

    turn_timestamps: list[datetime] = []
    tool_calls = 0
    tool_errors = 0
    cost_state = None

    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            if rec.get("type") == "cost-state":
                cost_state = rec

            if rec.get("type") == "assistant" and "timestamp" in rec:
                turn_timestamps.append(parse_ts(rec["timestamp"]))
                for block in rec.get("message", {}).get("content", []):
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_calls += 1

            if rec.get("type") == "user":
                content = rec.get("message", {}).get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            c = block.get("content")
                            text = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
                            if any(k in text for k in ("requires approval", "ERROR", "denied", "error")):
                                tool_errors += 1

    print(f"모델 호출(턴) 수: {len(turn_timestamps)}")
    print(f"도구 호출 수: {tool_calls}")
    print(f"도구 오류/승인거부로 보이는 결과 수: {tool_errors}")

    if len(turn_timestamps) >= 2:
        gaps = [
            (b - a).total_seconds()
            for a, b in zip(turn_timestamps, turn_timestamps[1:])
        ]
        gaps.sort()
        print(f"\n턴 사이 지연 시간(초): {[round(g, 2) for g in gaps]}")
        print(f"  최소 {gaps[0]:.2f}s / 중앙값 {gaps[len(gaps)//2]:.2f}s / 최대 {gaps[-1]:.2f}s")

    if cost_state:
        total_ms = cost_state.get("totalDuration", 0)
        tool_ms = cost_state.get("totalToolDuration", 0)
        model_ms = max(total_ms - tool_ms, 0)
        cost = cost_state.get("totalCostUSD", 0)
        print(f"\n--- cost-state (Claude Code가 공식 집계한 값) ---")
        print(f"총 소요 시간: {total_ms:,}ms")
        print(f"  └ 도구 실행 시간: {tool_ms:,}ms ({tool_ms/total_ms*100 if total_ms else 0:.1f}%)")
        print(f"  └ 모델 처리 시간(추정): {model_ms:,}ms ({model_ms/total_ms*100 if total_ms else 0:.1f}%)")
        print(f"총 비용: ${cost:.4f}")
    else:
        print("\ncost-state 레코드를 찾지 못했다 (세션이 아직 끝나지 않았을 수 있다).")


def main() -> None:
    cwd = Path.cwd()
    log_dir = project_log_dir(cwd)
    sessions = list_sessions(log_dir)
    if not sessions:
        print(f"세션 파일을 찾지 못했습니다: {log_dir}")
        sys.exit(1)

    args = sys.argv[1:]
    if args:
        matches = [p for p in sessions if args[0] in p.stem]
        target = matches[-1] if matches else sessions[-1]
    else:
        target = sessions[-1]

    report(target)


if __name__ == "__main__":
    main()
