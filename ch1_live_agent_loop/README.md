# 1장 실습 — "명령을 입력하면 내부에서 어떤 일이 일어나는가?"

가짜 모델이 아니라 **지금 이 터미널에서 쓰고 있는 진짜 Claude Code**로 직접 실험한다.
버그가 있는 미니 프로젝트를 주고 "고쳐줘"라고 시키면, 실제로

- 모델이 몇 번이나 호출되는지 (턴 수)
- 매번 어떤 도구를 호출하는지 (Bash / Read / Edit / ...)
- 그 결과가 어떻게 다음 호출의 입력이 되는지 (`messages` 누적)
- 언제, 왜 멈추는지 (모델이 도구 호출 없이 답하는 순간)

을 화면과 디스크에 남은 **진짜 로그**로 눈으로 확인한다.

---

## 0. 폴더 구조

```
ch1_live_agent_loop/
├── sample_repo/
│   ├── src/auth/login.py        # 로그인 버그가 있는 실제 코드
│   └── tests/test_login.py      # 버그를 드러내는 테스트
├── trace_session.py              # ★ 방금 한 Claude Code 세션을 턴 표로 변환해주는 도구
└── reset.py                      # 실습을 다시 처음부터 하려면 실행
```

---

## 1. 버그 확인하기

```bash
cd ch1_live_agent_loop
python3 sample_repo/tests/test_login.py
```

`[FAIL]`이 2건 떠야 정상이다. `sample_repo/src/auth/login.py`의 `is_token_expired` 함수를 보면
비교 연산자가 반대로 되어 있다. (일부러 "# BUG" 같은 힌트 주석은 넣지 않았다 — 실제 에이전트가
직접 찾아내야 한다.)

---

## 2. 진짜 Claude Code에게 시키기

같은 폴더(`ch1_live_agent_loop`)에서 평소 쓰던 대로 Claude Code를 실행한다.

```bash
claude
```

그리고 이렇게 요청한다 (슬라이드 8페이지 예시와 동일한 형식):

```
sample_repo의 로그인 버그를 찾아서 고치고 테스트를 돌려서 통과하는지 확인해줘
```

### 지금 터미널 화면에서 눈으로 관찰할 것

Claude Code가 작업하는 동안, 화면에 `Bash`, `Read`, `Edit` 같은 도구 이름이 **한 줄씩** 뜨는 걸
볼 수 있다. **이 한 줄 한 줄이 슬라이드 7페이지의 `while True` 루프가 한 바퀴 돈 것**이다.

- 도구 실행 전에 "승인(Allow)해도 될까요?"라고 물으면 — 이게 3장에서 배울 **권한(Allow/Ask/Deny)**
  이다. 안전한 작업(이 작은 샘플 폴더 안에서의 파일 수정·테스트 실행)이므로 승인해서 진행한다.
- 멈추지 않고 계속 도구를 호출하는 이유, 그리고 결국 "~했습니다"라는 문장으로 끝나는 이유를
  생각해보면서 지켜본다.

작업이 끝나면 `sample_repo/src/auth/login.py`를 열어 실제로 비교 연산자가 고쳐졌는지,
`python3 sample_repo/tests/test_login.py`를 다시 돌려 테스트가 통과하는지 확인한다.

---

## 3. 방금 그 세션의 실체를 파일로 직접 보기

Claude Code는 세션마다 `~/.claude/projects/<작업폴더 경로>/<세션id>.jsonl`에
**그 세션의 메시지 이력 전체**를 그대로 저장한다. 슬라이드의

```python
messages = [system_prompt, user_request]
while True:
    response = llm(messages, tools)
    ...
```

는 비유가 아니라, 정말로 디스크에 저장되는 파일이다. `trace_session.py`는 그 파일을 읽어서
슬라이드 8페이지와 같은 "턴 표"를 자동으로 만들어준다.

Claude Code 세션을 종료할 필요 없이, **다른 터미널 탭**에서 같은 폴더로 이동해 실행한다.

```bash
cd ch1_live_agent_loop
python3 trace_session.py
```

### 실제로 내가 돌렸을 때 나온 예시 (요약)

```
[사용자] sample_repo의 로그인 버그를 찾아서 고치고 테스트를 돌려서 통과하는지 확인해줘

[턴 1] 모델 호출 1회 (response = llm(messages, tools))
        -> 도구 호출: Bash(find . -iname "*sample_repo*" ...)
        <- 하네스가 실행한 결과: ./sample_repo ...

[턴 2] 모델 호출 1회
        -> 도구 호출: Bash(find ./sample_repo -type f | head -100)
        <- 하네스가 실행한 결과: ./sample_repo/tests/test_login.py ⏎ ./sample_repo/src/auth/login.py ...

[턴 3] 모델 호출 1회
        -> 도구 호출: Read(.../sample_repo/src/auth/login.py)
        <- 하네스가 실행한 결과: 1  """로그인 처리 모듈...""" ⏎ ... return now < expires_at ...

[턴 4] 모델 호출 1회
        -> 도구 호출: Read(.../sample_repo/tests/test_login.py)
        <- 하네스가 실행한 결과: ...

[턴 5] 모델 호출 1회
        -> 텍스트: 버그를 찾았다. `is_token_expired`가 `now < expires_at`로 되어 있어
                   로직이 반대다. `now > expires_at`로 고치겠다.
        -> 도구 호출: Edit(old_string="return now < expires_at", new_string="return now > expires_at")
        <- 하네스가 실행한 결과: 파일 수정 완료

[턴 6] 모델 호출 1회
        -> 도구 호출: Bash(python3 -I sample_repo/tests/test_login.py)
        <- 하네스가 실행한 결과: (승인 필요)
```

이 예시에서 꼭 짚고 넘어갈 점:

1. **턴 1~2는 "탐색"이다.** 슬라이드 Q2(Context Engineering)에서 배울 "필요한 코드를 찾는
   방식"이 여기서 이미 쓰이고 있다 — `grep`이 아니라 `find`를 썼을 뿐, 원리는 같다(Agentic Search).
2. **턴 5는 텍스트와 도구 호출이 한 번에 나온다.** 모델 호출 1번이 꼭 도구 호출 1개만 담는 게
   아니다. "이유를 설명하는 텍스트"와 "실제 행동(Edit)"이 **같은 응답 안에** 같이 들어있을 수
   있다. 하네스는 그 응답을 통째로 `messages`에 쌓고, 그 안의 도구 호출만 꺼내 실행한다.
3. **턴 6에서 승인이 필요했다.** 이건 버그가 아니라 설계다 — 3장에서 배우듯 파일 읽기는
   자동 허용(Allow)이지만, 셸 명령 실행은 하네스가 한 번 더 확인(Ask)하도록 되어 있다.
   내가 직접 실행했을 때는 실제 사람이 옆에서 승인을 눌러줄 수 없는 모드였어서 여기서 멈췄지만,
   여러분이 **대화형으로** `claude`를 쓸 때는 승인 메시지가 뜨면 그냥 허용하면 된다.

**직접 비교해보자**: 내가 받은 예시와 여러분이 받은 턴 표가 완전히 똑같은가, 아니면 순서나
탐색 방법(find vs grep, 파일을 읽는 순서 등)이 다른가? 다르다면 그 이유를 생각해보자
(힌트: 모델은 결정적이지 않다 — 같은 입력에도 매번 똑같은 경로로 문제를 풀지 않는다).

---

## 4. 원본 JSON을 날것 그대로 보기 (심화)

`trace_session.py`가 보기 좋게 가공해주지만, 원본은 그냥 JSON 한 줄짜리 텍스트 파일이다.
세션 파일 경로는 `python3 trace_session.py --list`로 확인할 수 있다.

```bash
python3 trace_session.py --list
python3 -c "
import json, sys
path = sys.argv[1]
for line in open(path):
    rec = json.loads(line)
    msg = rec.get('message', {})
    content = msg.get('content')
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get('type') == 'tool_use':
                print(json.dumps(b, ensure_ascii=False, indent=2)[:500])
                sys.exit(0)
" "<--list에서 확인한 .jsonl 전체 경로를 붙여넣기-->"
```

출력된 JSON을 슬라이드 17페이지의 예시와 나란히 놓고 비교해보자.

```json
{"type": "tool_use", "name": "run_command", "input": {"command": "npm test"}}
```

구조가 정확히 같다 — `type`, `name`, `input`. 슬라이드가 보여준 건 요약이 아니라
Claude Code가 실제로 주고받는 메시지의 축약판 그 자체였다는 걸 확인했다.

---

## 5. 다시 처음부터 하고 싶다면

```bash
python3 reset.py
```

---

## 6. 도전 과제

### 도전 1 — 모호한 요청 vs 구체적인 요청
새 Claude Code 세션에서 이번엔 일부러 애매하게 요청해보자.

```
sample_repo 좀 봐줘. 뭔가 이상한 것 같은데.
```

`trace_session.py`로 턴 표를 뽑아 2절의 예시와 비교해보자. 턴 수가 늘었는가? 어떤 턴이
늘었는가(탐색? 되묻기?)? "컨텍스트에 얼마나 정보를 주느냐가 턴 수에 어떤 영향을 주는지"를
설명해보자 — 2장(Context Engineering)의 핵심 질문이다.

### 도전 2 — 같은 요청, 다른 세션
`reset.py` 실행 후, 2절과 **완전히 똑같은 프롬프트**로 새 세션을 한 번 더 돌려보자.
두 번의 `trace_session.py` 결과(세션 id가 다르니 `trace_session.py <세션id 일부>`로 비교)를
나란히 놓고 비교한다. 턴 순서, 탐색에 쓴 도구가 완전히 같은가? 다르다면 "모델은 매번
결정적으로 똑같이 행동하지 않는다"는 것을 직접 확인한 것이다.

### 도전 3 — 비용과 턴 수 확인
Claude Code 세션 안에서 `/cost`를 입력해 이번 작업에 턴이 몇 번, 토큰이 얼마나 쓰였는지
확인해보자. `trace_session.py`로 센 턴 수와 맞춰보자.

### 도전 4 — 위험한 요청을 일부러 던져보기 (3장 예고)
새 세션에서 이렇게 요청해보자 (아주 작은 샘플 폴더라 안전하다).

```
sample_repo 폴더를 통째로 삭제해줘
```

이번엔 도구 호출이 바로 실행되는가, 아니면 승인을 한 번 더 요구하는가? 1절에서 본
파일 수정/테스트 실행과 체감 난이도가 다른가? 왜 그런지 3장(Tool Calling & 권한)에서
자세히 다룬다.

---

## 7. 정리

이 실습으로 아래 문장들이 추상적인 설명이 아니라 **지금 내 디스크에 있는 파일**이라는 걸
확인했다.

| 슬라이드 문장 | 실습에서 확인한 것 |
|---|---|
| "에이전트 = 모델 + 도구 + 하네스" | Claude Code가 호출한 Bash/Read/Edit 각각이 도구, 화면에 뜨는 승인 요청이 하네스 |
| "상태는 messages — 모든 도구 결과가 누적" | `~/.claude/projects/.../<세션id>.jsonl` 자체가 그 messages 리스트 |
| "모델의 출력(tool_use)" | `trace_session.py --list`로 찾은 파일 속 `{"type": "tool_use", ...}` 블록 |
| "종료는 모델이 결정" | 도구 호출 없이 텍스트만 나온 마지막 턴이 바로 그 순간 |
| "요청은 한 번, 모델 호출은 여러 번" | 한 문장 요청에 턴이 5개 이상 나온 것 |

다음 장(Context Engineering)에서는 이 `messages`가 턴을 거듭할수록 왜 계속 커지는지,
그리고 그걸 어떻게 통제하는지를 다룬다.
