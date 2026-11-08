# 4장 실습 — "복잡한 작업을 어떻게 나누고 협력하는가?"

1~3장과 같은 방식이다: 실제 Claude Code에게 "혼자 다 하지 말고 나눠서 시켜봐"라고
요청하고, 실제로 무슨 일이 일어나는지 로그로 들여다본다.

- 오케스트레이터(주 에이전트)가 작업을 나눠서 **서브에이전트**에게 맡기는 걸 직접 시킨다
- 서브에이전트가 한 일이 메인 대화에는 "요약"만 남고, **실제 탐색 과정은 완전히 분리된
  파일**에 저장된다는 걸 디스크에서 직접 확인한다 (슬라이드의 Isolation)

---

## 0. 폴더 구조

```
ch4_live_multi_agent/
├── sample_repo/
│   ├── mod_a.py       # 독립적인 버그 1
│   ├── mod_b.py       # 독립적인 버그 2
│   ├── mod_c.py       # 독립적인 버그 3
│   └── check_all.py   # 세 개가 모두 고쳐졌는지 한 번에 검증
├── trace_session.py    # 1~3장과 같은 도구
├── show_subagents.py   # ★ 서브에이전트의 "속사정"을 보여주는 새 도구
└── reset.py             # 실습을 다시 처음부터 하려면 실행
```

---

## 1. 버그 세 개 확인하기

```bash
cd ch4_live_multi_agent/sample_repo
python3 check_all.py
```

`[FAIL]`이 떠야 정상이다. `mod_a.py`, `mod_b.py`, `mod_c.py`는 서로 아무 관련이 없는
독립적인 파일이다 — 슬라이드 4장의 "적합한 경우: 서로 독립된 모듈·파일 단위 작업"에
정확히 해당한다.

---

## 2. 서브에이전트에게 나눠서 맡기기

```bash
claude
```

```
mod_a.py, mod_b.py, mod_c.py 세 파일에 각각 독립적인 버그가 있어. 세 개를 각각
별도의 서브에이전트에게 병렬로 맡겨서 찾아 고치게 해줘. mod_b.py의 greet 함수는
정확히 'Hello, Claude!' 형태(첫 글자만 대문자, 쉼표, 느낌표)로 인사해야 해.
끝나면 결과를 요약해줘
```

**실제로 내가 받은 결과**: 모델이 먼저 세 파일을 직접 훑어보고, 이렇게 말했다.

> "Each file's bug is clear. I'll dispatch three parallel subagents, each fixing one file."

그리고 `Agent` 도구를 세 번 연속 호출했다 (`subagent_type: "general-purpose"`). 각각
"Async agent launched successfully"라는 결과가 돌아왔고, 메인 세션은 곧바로

> "세 개의 서브에이전트를 병렬로 실행했습니다 — 완료되면 알림이 올 거예요."

라고 하고는 기다렸다. 잠시 후 서브에이전트들이 끝났다는 알림이 도착했고, 최종적으로
세 버그 모두 올바르게 고쳐졌다.

```bash
cat mod_a.py mod_b.py mod_c.py
python3 check_all.py
```

`전체 통과`가 나와야 한다.

---

## 3. trace_session.py로 "메인 에이전트가 본 것"만 확인하기

```bash
python3 ../trace_session.py
```

메인 세션의 턴 표에는 이렇게만 남는다 (실제로 내가 받은 결과를 축약):

```
[턴 6] 모델 호출 1회
        -> 텍스트: Each file's bug is clear. I'll dispatch three parallel subagents...
        -> 도구 호출: Agent({"description": "Fix bug in mod_a.py", "subagent_type": "general-purpose", ...})
        <- 하네스가 실행한 결과: Async agent launched successfully...

[턴 7] 모델 호출 1회
        -> 도구 호출: Agent({"description": "Fix bug in mod_b.py", ...})
[턴 8] 모델 호출 1회
        -> 도구 호출: Agent({"description": "Fix bug in mod_c.py", ...})

[턴 9] 모델 호출 1회
        -> 텍스트: 세 개의 서브에이전트를 병렬로 실행했습니다 — 완료되면 알림이 올 거예요.

[사용자] <task-notification> ... (서브에이전트 완료 알림)

[턴 12~14] 모델 호출 1회
        -> 도구 호출: Read(mod_a.py / mod_b.py / mod_c.py)   # 결과를 직접 재확인
[턴 15] 모델 호출 1회
        -> 텍스트: 세 작업 모두 완료됐고, 파일 내용도 직접 확인했습니다...
```

**주목할 점**: 메인 세션에는 서브에이전트가 각 파일을 **어떻게** 고쳤는지(어떤 줄을
읽었는지, 몇 번 시도했는지)가 전혀 안 보인다. `Agent(...)` 호출 한 번과 "완료됐다"는
알림, 그게 전부다. 슬라이드의 "작업 지시는 아래로, 요약된 결과는 위로"가 정확히 이
모습이다.

---

## 4. show_subagents.py로 "서브에이전트가 실제로 한 일" 들여다보기

메인 세션 파일에 없는 내용이 어디 있을까? Claude Code는 서브에이전트의 대화를
**완전히 별도의 파일**에 저장한다. 직접 찾아보자.

```bash
python3 ../show_subagents.py
```

**실제로 내가 받은 결과 (하나만 발췌)**:

```
## 서브에이전트: Fix bug in mod_b.py
   agentType=general-purpose  toolUseId=toolu_...  finished=True
   상세 로그 파일: ~/.claude/projects/.../<세션id>/subagents/agent-a386c2bdb51680cf0.jsonl
     -> 도구 호출: Read(mod_b.py)
     -> 도구 호출: Edit(mod_b.py)
     -> 도구 호출: Bash(python3 -I -c "from mod_b import greet; assert greet('cl...")
     -> 도구 호출: Bash(python3 -c "from mod_b import greet; assert greet('claud...")
     -> 최종 보고: I fixed the bug in mod_b.py. Change made: - Before: ... - After: ...
```

메인 에이전트가 "Agent 도구를 호출"한 그 한 줄 뒤에, 사실은 Read → Edit → Bash(검증
시도) → Bash(재시도)까지 포함된 **완전한 자기만의 Agent Loop**(1장!)가 통째로 돌아가고
있었다. 그 전체 과정은 메인 세션의 컨텍스트에는 전혀 쌓이지 않았다 — 오직
`show_subagents.py`가 찾아준 별도 파일에만 남아있다. 이게 "컨텍스트를 아낀다"는
Isolation의 실체다: 메인 에이전트의 `messages`가 서브에이전트의 탐색 과정 전체를
떠안지 않아도 된다.

---

## 5. 다시 처음부터

```bash
python3 reset.py
```

---

## 6. 도전 과제

### 도전 1 — 역할을 분리해보기 (작성자 vs 리뷰어)
새 세션에서 이렇게 요청해보자.

```
mod_a.py의 버그를 한 서브에이전트에게 고치게 한 다음, 그 결과를 다른 서브에이전트에게
리뷰시켜서 제대로 고쳤는지 확인해줘
```

`show_subagents.py`로 두 서브에이전트의 역할(설명)이 어떻게 다른지, 두 번째
서브에이전트의 프롬프트에 첫 번째 결과가 어떻게 전달됐는지 확인해보자.

### 도전 2 — 공유 파일을 동시에 건드리게 해서 실패를 유도해보기
`mod_a.py`와 `mod_b.py`를 **같은 서브에이전트 두 개**가 **동시에** 수정하도록
일부러 애매하게 요청해보자(예: "두 서브에이전트 모두에게 mod_a.py와 mod_b.py를 다
살펴보고 필요하면 고치라고 해줘"). 슬라이드 4장의 "피해야 할 경우: 여러 에이전트가
같은 파일을 동시 수정"이 왜 위험한지 실제로 충돌이나 중복 작업이 일어나는지
관찰해보자.

### 도전 3 — 단일 에이전트와 비교하기
`reset.py` 실행 후, 이번엔 서브에이전트를 쓰지 말고 요청해보자.

```
mod_a.py, mod_b.py, mod_c.py의 버그를 네가 직접 순서대로 찾아서 고쳐줘
```

`trace_session.py`로 턴 수와 전체 걸린 시간을 2절(서브에이전트 사용)과 비교해보자.
이렇게 작고 간단한 작업에서는 어느 쪽이 더 빠르고 간단한가? 슬라이드의
"에이전트가 늘수록 토큰 비용과 조정 비용도 늘어난다 — 이득이 비용보다 클 때만
나눈다"는 말이 이 비교에서 어떻게 보이는지 설명해보자.

### 도전 4 — git worktree로 진짜 병렬 실행 체감하기 (심화)
지금은 세 서브에이전트가 "같은 폴더" 안의 서로 다른 파일을 고쳤다. 만약 같은 파일을
두 가지 다른 방식으로 동시에 실험해보고 싶다면? `git worktree add`로 같은 저장소의
복사본을 두 개 만들고, 각 작업 공간에서 서로 다른 Claude Code 세션을 띄워 같은
파일을 독립적으로 수정해보자(슬라이드의 "병렬 실행: 독립된 작업을 git worktree 같은
분리된 작업 공간에서 동시에 진행"). 끝난 뒤 `git diff`로 두 결과를 비교해본다.

---

## 7. 정리

| 슬라이드 문장 | 실습에서 확인한 것 |
|---|---|
| "오케스트레이터가 계획하고, 하위 작업을 서브에이전트에 맡긴 뒤 결과를 통합" | 메인 세션이 `Agent` 도구로 세 작업을 위임하고, 끝난 뒤 직접 Read로 재확인·요약한 것 |
| "작업 지시는 아래로, 요약된 결과는 위로" | 메인 세션엔 "Agent(...)" 호출과 완료 알림만, 상세 과정은 `show_subagents.py`로만 보이는 것 |
| "병렬 실행" | 세 `Agent` 호출이 연달아 일어나고 "Async agent launched"로 동시에 진행된 것 |
| "독립된 작업을 나눈다" | mod_a/b/c가 서로 참조하지 않는 완전히 독립적인 파일이었던 것 |
| "같은 파일을 동시 수정하면 위험" | 도전 과제 2에서 직접 충돌을 유도해 확인 |
| "이득이 비용보다 클 때만 나눈다" | 도전 과제 3에서 단일 에이전트와 턴 수·시간을 직접 비교 |

다음 장(성능 최적화와 장애 분석)에서는 지금까지 trace_session.py로 계속 봐왔던
"컨텍스트 크기"와 턴 수가 실제로 비용·시간과 어떻게 연결되는지, 그리고 에이전트가
틀렸을 때 그 원인을 어떻게 추적하는지를 다룬다.
