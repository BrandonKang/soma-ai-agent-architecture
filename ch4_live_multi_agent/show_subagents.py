"""서브에이전트에게 위임된 작업의 "속사정"을 보여준다.

trace_session.py로 메인 세션을 보면 "Agent" 도구 호출 한 줄과 그 요약 결과만
보인다 — 슬라이드의 "Isolation: 탐색은 별도 컨텍스트에서 하고 요약만 주
에이전트에 돌려준다"가 바로 이것이다. 그런데 서브에이전트가 실제로 무슨 작업을
했는지는 메인 세션 파일이 아니라, 같은 세션 폴더 아래
<세션id>/subagents/agent-<id>.jsonl 에 "따로" 저장된다.

이 스크립트는 그 파일들을 찾아서 각 서브에이전트가 실제로 어떤 도구를 몇 번
호출했는지, 메타데이터는 무엇인지 보여준다.

사용법 (claude를 실행했던 폴더, 즉 sample_repo 안에서):
    python3 ../show_subagents.py                # 가장 최근 세션
    python3 ../show_subagents.py <세션id 일부>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from trace_session import list_sessions, project_log_dir, short  # type: ignore


def find_subagent_dir(session_jsonl: Path) -> Path:
    return session_jsonl.parent / session_jsonl.stem / "subagents"


def print_subagent(meta_path: Path) -> None:
    meta = json.loads(meta_path.read_text())
    jsonl_path = meta_path.with_suffix("").with_suffix(".jsonl")

    print(f"## 서브에이전트: {meta.get('description')}")
    print(f"   agentType={meta.get('agentType')}  toolUseId={meta.get('toolUseId')}  "
          f"finished={meta.get('finished')}")
    print(f"   상세 로그 파일: {jsonl_path}")

    if not jsonl_path.exists():
        print("   (아직 로그 파일이 생성되지 않았다 — 서브에이전트가 진행 중일 수 있다)\n")
        return

    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "assistant":
                continue
            for block in rec.get("message", {}).get("content", []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    print(f"     -> 도구 호출: {block.get('name')}({short(block.get('input'), 70)})")
                elif block.get("type") == "text" and block.get("text", "").strip():
                    print(f"     -> 최종 보고: {short(block['text'], 200)}")
    print()


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

    subagent_dir = find_subagent_dir(target)
    print(f"# 메인 세션: {target}")
    print(f"# 서브에이전트 폴더: {subagent_dir}\n")

    if not subagent_dir.exists():
        print("이 세션에서는 서브에이전트를 호출하지 않았다.")
        print("README 2절의 요청(서브에이전트에게 위임하는 요청)으로 다시 시도해보라.")
        return

    metas = sorted(subagent_dir.glob("*.meta.json"))
    if not metas:
        print("서브에이전트 메타 파일을 찾지 못했다.")
        return

    for meta_path in metas:
        print_subagent(meta_path)


if __name__ == "__main__":
    main()
