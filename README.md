# AI 코딩 에이전트의 내부 아키텍처와 엔지니어링 — 실습 저장소

이 저장소는 강의 자료 **「AI 코딩 에이전트의 내부 아키텍처와 엔지니어링」**의 핸즈온 랩입니다.
가짜 모델이나 시뮬레이션이 아니라, **지금 이 터미널에서 쓰는 진짜 Claude Code**로
에이전트 루프·컨텍스트·도구 권한·멀티 에이전트·성능·보안을 직접 관찰합니다.

이론 슬라이드와 PDF는 저장소 루트의
[`AI 코딩 에이전트의 내부 아키텍처와 엔지니어링.pdf`](./AI%20코딩%20에이전트의%20내부%20아키텍처와%20엔지니어링.pdf)
에 있습니다. 각 장 실습의 **전체 단계·관찰 포인트·도전 과제**는 해당 장의 `README.md`에 있습니다.

---

## 무엇을 / 왜 하는가

코딩 에이전트는 “한 번 물어보고 한 번 답하는” 챗봇이 아닙니다.
요청 한 줄에 모델이 **여러 번** 호출되고, 도구(Bash / Read / Edit / …) 결과가
`messages`에 쌓이며, 하네스가 권한을 검사한 뒤 실행하고, 모델이 도구 없이 답하는
순간에 루프가 끝납니다.

이 랩의 목표는 그 흐름을 슬라이드 문장으로만 외우는 것이 아니라,
세션 로그(`.jsonl`)와 `trace_session.py` 등으로 **디스크에 남은 실체**로 확인하는 것입니다.

- 버그가 있는 `sample_repo`에 Claude Code로 “고쳐줘”를 시킨다
- 턴 수, 도구 호출, 컨텍스트 크기, 승인(Allow/Ask/Deny), 서브에이전트 격리 등을 관찰한다
- `reset.py`로 초기화한 뒤 같은 실험을 반복한다

---

## 누구를 위한가

- AI 코딩 에이전트(특히 Claude Code)가 **내부에서 어떻게 도는지** 이해하고 싶은 개발자·엔지니어
- 컨텍스트 엔지니어링, 도구 권한, MCP, 멀티 에이전트, 운영 지표를 **실습으로** 잡고 싶은 학습자
- 슬라이드/PDF의 개념을 자기 머신에서 재현해 보고 싶은 강의 수강생

에이전트를 “잘 쓰는 팁” 모음이 아니라, **루프·상태·권한·격리·관측**을 중심으로 구성했습니다.

---

## 사전 요구사항

| 항목 | 설명 |
|---|---|
| **Claude Code** | 로컬에 설치된 실제 Claude Code (`claude` CLI). 랩은 이 도구로 진행합니다. |
| **Python 3** | `trace_session.py`, `reset.py`, 샘플 테스트·스크립트 실행용 |
| **터미널** | 실습 폴더에서 `claude`를 실행하고, 다른 탭에서 트레이스 스크립트를 돌릴 수 있으면 됩니다 |

추가 프레임워크나 가짜 LLM 서버는 필요 없습니다.

---

## 저장소 구조

```
soma-ai-agent-architecture/
├── README.md                                          # 이 파일
├── AI 코딩 에이전트의 내부 아키텍처와 엔지니어링.pdf   # 강의 PDF
├── ch1_live_agent_loop/                               # 에이전트 루프
├── ch2_live_context_engineering/                      # 컨텍스트 / CLAUDE.md
├── ch3_live_tool_calling_mcp/                         # 권한 + toy MCP
├── ch4_live_multi_agent/                              # 오케스트레이터 + 서브에이전트
├── ch5_live_performance_debugging/                    # 성능·애매한 버그 진단
└── ch6_live_quality_security_ops/                     # 보안 모의 공격 + 운영 리포트
```

장마다 대체로 다음이 있습니다.

- `sample_repo/` — 일부러 심어 둔 버그·시나리오가 있는 미니 프로젝트
- `README.md` — 해당 장 실습의 전체 절차
- `trace_session.py` — Claude Code 세션 로그를 턴 표로 변환
- `reset.py` — 샘플을 초기 상태로 되돌림
- (일부 장) `session_timing.py`, `show_subagents.py`, `CLAUDE.md.example`, `toy_mcp_server.py` 등

---

## 장별 안내

| 장 | 폴더 | 한 줄 요약 |
|---|---|---|
| 1 | [ch1_live_agent_loop](./ch1_live_agent_loop/) | 에이전트 루프: 턴, 도구 호출, `messages` 누적, 종료 조건 |
| 2 | [ch2_live_context_engineering](./ch2_live_context_engineering/) | 같은 요청에 `CLAUDE.md` 유무가 결과에 미치는 영향, 컨텍스트 증가 |
| 3 | [ch3_live_tool_calling_mcp](./ch3_live_tool_calling_mcp/) | Allow / Ask / Deny 권한과 직접 만든 toy MCP 서버 연결 |
| 4 | [ch4_live_multi_agent](./ch4_live_multi_agent/) | 오케스트레이터가 서브에이전트에 위임하고, 탐색은 격리된 로그에만 남는 것 |
| 5 | [ch5_live_performance_debugging](./ch5_live_performance_debugging/) | 세션 타이밍 공식과 애매한 버그(코드 vs 테스트) 진단 |
| 6 | [ch6_live_quality_security_ops](./ch6_live_quality_security_ops/) | 프롬프트 인젝션·시크릿 모의 공격과 운영용 트레이스/타이밍 리포트 |

### 1장 — 에이전트 루프

로그인 버그가 있는 `sample_repo`를 고치게 시킨 뒤, `trace_session.py`로
턴마다 어떤 도구가 호출됐는지, 결과가 다음 입력에 어떻게 쌓이는지,
모델이 도구 없이 답할 때 루프가 끝나는지를 확인합니다.

### 2장 — 컨텍스트 엔지니어링

완전히 같은 요청을 `CLAUDE.md` 없이 / 있이 두 번 실행해 결과가 달라지는지 보고,
턴이 지날수록 컨텍스트(토큰)가 커지는 것을 숫자로 확인합니다.

### 3장 — 도구 호출과 MCP

`.claude/settings.json`의 Deny/Ask로 Bash 실행을 막거나 승인을 요구해 보고,
`toy_mcp_server.py`(주사위 굴리기)를 MCP로 등록해 외부 프로그램이 도구로 들어오는 과정을 봅니다.

### 4장 — 멀티 에이전트

독립적인 버그가 있는 세 파일을 서브에이전트에 나눠 맡기고,
메인 세션에는 요약만 남고 상세 탐색은 `show_subagents.py`로만 보이는 Isolation을 확인합니다.

### 5장 — 성능과 장애 분석

`session_timing.py`로 “작업 시간 ≈ 모델 호출 횟수 × 처리 시간 + 도구 실행 시간”을
실제 세션 숫자로 확인하고, 코드는 맞고 테스트 기댓값이 틀린 애매한 실패를 진단하게 합니다.

### 6장 — 품질·보안·운영

회의록에 숨긴 프롬프트 인젝션과 가짜 `.env` 시크릿으로 **안전한 모의 공격**을 시도합니다.
(샘플 `.env`와 공격 문구는 실제 위협이 아닌 교육용 페이크입니다.)
이어 `trace_session.py` / `session_timing.py`를 운영 리포트처럼 묶어 봅니다.

---

## 실습을 시작하는 방법 (공통)

장마다 세부 프롬프트와 관찰 포인트는 다르지만, 큰 흐름은 같습니다.

1. 해당 장 폴더(또는 그 안의 `sample_repo`)로 이동합니다.
2. 필요하면 샘플 테스트·스크립트로 **초기 실패/상태를 확인**합니다.
3. `claude`로 Claude Code를 실행하고, 장 README에 적힌 요청을 입력합니다.
4. 작업 중 도구 이름·승인 요청·서브에이전트 위임 등을 화면에서 관찰합니다.
5. 다른 터미널에서 `python3 trace_session.py`(및 해당 장의 보조 스크립트)로 세션을 분석합니다.
6. 다시 하려면 `python3 reset.py`로 초기화합니다.

**상세 단계, 예시 트레이스, 도전 과제는 반드시 각 장의 `README.md`를 따르세요.**
이 루트 README는 지도일 뿐, 실습 교재의 본문은 장별 README입니다.

---

## 강의 PDF

개념·다이어그램·슬라이드 본문은 루트의 PDF를 참고하세요.

- [`AI 코딩 에이전트의 내부 아키텍처와 엔지니어링.pdf`](./AI%20코딩%20에이전트의%20내부%20아키텍처와%20엔지니어링.pdf)

실습은 PDF의 각 장을 손으로 검증하는 용도이며, 1장부터 6장까지 모두 **실제 Claude Code**로
확인할 수 있도록 맞춰 두었습니다.
