# 3장 실습 — "도구를 어떻게 선택·실행하고 외부와 연결하는가?"

1·2장과 같은 방식이다: 실제 Claude Code로 실험한다. 이번엔 두 가지를 확인한다.

1. **Allow/Ask/Deny**가 말뿐인 설명이 아니라, 프로젝트에 파일 하나(`.claude/settings.json`)만
   놓으면 실제로 도구 실행을 막거나 승인을 요구하는 실제 동작이라는 것
2. **MCP**가 "외부 시스템을 도구로 연결하는 표준"이라는 게 무슨 뜻인지 — 내가 직접 만든
   아주 작은 외부 프로그램을 Claude Code가 실제로 도구처럼 호출하는 걸 눈으로 보는 것

---

## 0. 폴더 구조

```
ch3_live_tool_calling_mcp/
├── sample_repo/
│   ├── runme.py             # 권한 실습용 간단한 스크립트
│   └── toy_mcp_server.py    # 내가 직접 만든 최소 MCP 서버 (도구 1개: 주사위 굴리기)
├── trace_session.py         # 1·2장과 같은 도구
└── reset.py                 # 실습을 다시 처음부터 하려면 실행
```

---

## 1. Allow / Ask / Deny — 설정 파일 하나로 도구 실행을 막아보기

`sample_repo` 안에 Claude Code 프로젝트 권한 설정 파일을 만든다.

```bash
cd ch3_live_tool_calling_mcp/sample_repo
mkdir -p .claude
cat > .claude/settings.json <<'EOF'
{
  "permissions": {
    "deny": ["Bash(python3:*)"]
  }
}
EOF
```

이 설정은 "`python3`로 시작하는 모든 Bash 명령은 무조건 차단(Deny)한다"는 규칙이다.
이제 Claude Code를 실행해서 요청해본다.

```bash
claude
```

```
runme.py를 python3로 실행해서 출력 결과를 알려줘
```

**실제로 내가 받은 결과**: 모델이 `Bash(python3 runme.py)`를 호출하려 했지만

> "`python3 runme.py` 실행 권한이 거부되었습니다. 이 샘플 저장소가 권한 관련 검증용으로
> 보이는데, 의도적으로 차단 설정이 되어 있는 것 같습니다."

라고 답했다 — **모델이 승인을 요청하지도 않았다.** `deny`는 "물어보지도 않고 막는다"는
뜻이기 때문이다. (반대로 설정을 `"ask"`로 바꾸면, 하네스가 실행 직전에 사람에게
"이 명령을 실행해도 될까요?"라고 묻는 **승인 대화상자**가 뜬다 — 지금까지 1·2장에서
`claude`를 쓸 때 Bash/Edit 앞에서 봤던 바로 그 화면이다.)

`settings.json`의 `"deny"`를 `"ask"`로 바꿔서 새 세션으로 같은 요청을 다시 해보고,
두 경우의 차이를 직접 느껴보자 — **deny는 차단, ask는 승인 요청**이다.

---

## 2. MCP — 내가 만든 외부 프로그램을 Claude Code의 도구로 연결하기

`sample_repo/toy_mcp_server.py`를 열어보자. 외부 라이브러리 없이 표준입출력으로
JSON 메시지만 주고받는 아주 작은 프로그램이다. 도구를 딱 하나만 제공한다 —
**주사위 굴리기**. Claude Code에는 이런 기능이 원래 없다. 그래서 이게 실제로
동작하면 "MCP를 통해 외부 기능이 도구로 들어왔다"는 걸 의심할 여지 없이 확인할 수 있다.

먼저 차단 설정을 지운다.

```bash
rm .claude/settings.json
```

MCP 서버로 등록한다.

```bash
claude mcp add toy-dice -- python3 "$(pwd)/toy_mcp_server.py"
claude mcp list
```

`toy-dice: ... - ✔ Connected`가 떠야 한다. 이제 Claude Code를 실행해 요청한다.

```bash
claude
```

```
6면체 주사위를 2번 굴려줘
```

처음엔 "주사위 도구 사용 권한이 필요합니다"라는 승인 요청이 뜰 수 있다 — MCP로 들어온
도구도 똑같이 Allow/Ask/Deny 대상이기 때문이다. 승인하면 실제로 숫자가 나온다.

**실제로 내가 받은 결과**: `6면체 주사위를 두 번 굴린 결과: **5**, **1**`
(당연히 매번 다른 숫자가 나온다 — 진짜로 내 `toy_mcp_server.py`의 `random.randint`가
실행된 것이다.)

---

## 3. trace_session.py로 MCP 도구 호출 확인하기

```bash
python3 ../trace_session.py
```

**실제로 내가 받은 결과 (일부)**:

```
[턴 N] 모델 호출 1회
        -> 도구 호출: mcp__toy-dice__roll_dice({"sides": 6})
```

도구 이름이 `mcp__toy-dice__roll_dice` 형태다. 슬라이드의 MCP Host 다이어그램에서
"서버마다 MCP 클라이언트 연결"이라고 했던 게 바로 이것이다 — Claude Code(호스트)가
`toy-dice`라는 서버에 연결해서, 그 서버가 제공하는 `roll_dice` 도구를
`mcp__toy-dice__roll_dice`라는 이름으로 모델에게 노출한 것이다. 서버 이름과 도구 이름이
합쳐져 있으니, 서버가 여러 개여도 이름이 겹칠 걱정이 없다.

---

## 4. 원본에서 도구 정의 직접 보기 (심화)

`toy_mcp_server.py`의 `TOOLS` 리스트를 다시 보자.

```python
TOOLS = [
    {
        "name": "roll_dice",
        "description": "N면체 주사위를 굴려서 나온 숫자를 반환한다.",
        "inputSchema": {
            "type": "object",
            "properties": {"sides": {"type": "integer", "description": "주사위 면 수"}},
            "required": ["sides"],
        },
    }
]
```

이게 슬라이드 14페이지의 "도구 정의(요청에 포함)" 예시(`{"name": ..., "description": ...,
"input_schema": ...}`)와 정확히 같은 모양이다. **이 파일을 내가 직접 썼다**는 게
핵심이다 — MCP는 이 평범한 JSON 스키마 하나만 표준 방식으로 노출하면, Claude Code든
다른 어떤 MCP 호스트든 그대로 가져다 쓸 수 있게 해주는 약속일 뿐이다.

좋은 도구의 조건(슬라이드 14페이지)에 비춰 `toy_mcp_server.py`의 `roll_dice`를 평가해보자.

- 이름과 설명이 명확한가?
- 입력 스키마가 모델이 헷갈리지 않게 되어 있는가?
- 만약 `sides`에 음수나 0을 넣으면 어떻게 될까? ("행동 가능한 오류" 원칙과 연결해서
  직접 `sides: 0`으로 호출해보고, 에러 처리가 없다는 걸 확인해보자 — 5절 도전 과제에서
  고쳐본다.)

---

## 5. 다시 처음부터

```bash
python3 reset.py
```

`settings.json` 삭제, `toy-dice` MCP 서버 등록 해제까지 한 번에 처리한다.

---

## 6. 도전 과제

### 도전 1 — Ask를 직접 승인해보기
`.claude/settings.json`을 `{"permissions": {"ask": ["Bash(python3:*)"]}}`로 바꾸고
(대화형) `claude`를 실행해 1절과 같은 요청을 해보자. 이번엔 터미널에 승인 대화상자가
뜬다. 허용해서 진행해보고, "한 번만 허용" vs "이후로도 계속 허용"의 차이도 살펴보자.

### 도전 2 — 허술한 도구를 고쳐보기
4절에서 발견한 문제(`sides: 0` 또는 음수를 넣었을 때 에러 처리가 없는 것)를
`toy_mcp_server.py`에 직접 고쳐보자. `tools/call` 처리 부분에 유효성 검사를 추가해서,
잘못된 입력이면 `error` 대신 "행동 가능한 오류 메시지"(예: "sides는 2 이상이어야
합니다")를 `content`로 돌려주게 만들어보자. 그리고 Claude Code에게 일부러
`0면체 주사위를 굴려줘`라고 요청해서, 모델이 그 에러 메시지를 보고 어떻게 반응하는지
관찰해보자.

### 도전 3 — 도구를 하나 더 추가해보기
`toy_mcp_server.py`에 두 번째 도구(예: `flip_coin` — 동전 던지기)를 추가해보자.
`TOOLS` 리스트에 정의를 추가하고 `tools/call` 분기를 하나 더 만들면 된다. 다시
`claude mcp list`로 서버가 여전히 연결돼 있는지 확인하고(코드만 바꿨다면 재등록 없이도
다음 세션부터 반영된다), 새 세션에서 두 도구를 모두 써보라고 요청해보자.

### 도전 4 — 허용 범위를 더 세밀하게
`settings.json`의 deny 패턴을 `"Bash(python3:*)"`(전체 차단) 대신
`"Bash(python3 runme.py:*)"`처럼 더 좁혀보자. 그러면 `runme.py` 실행은 막히지만 다른
`python3` 스크립트 실행은 막히지 않는다. 패턴을 좁히고 넓히는 것이 실무에서
"필요한 것만 정확히 차단/허용"하는 것과 어떻게 연결되는지 설명해보자.

---

## 7. 정리

| 슬라이드 문장 | 실습에서 확인한 것 |
|---|---|
| "도구 정의가 요청에 포함된다" | `toy_mcp_server.py`의 `TOOLS` 스키마가 그대로 모델에게 전달된 것 |
| "하네스가 권한을 확인하고 실제로 실행" | `.claude/settings.json`의 `deny` 규칙이 Bash 호출을 막은 것 |
| "Allow / Ask / Deny" | 차단(아예 안 물어봄) vs 승인 요청(물어보고 허락 받음)의 차이 |
| "MCP: 서버를 한 번 만들면 여러 에이전트에서 재사용" | `claude mcp add`로 등록한 서버가 세션마다 다시 연결되는 것 |
| "Tools / Resources / Prompts" | 이번엔 Tools만 다뤘다 — `roll_dice` 하나가 바로 그 Tools다 |
| "도구 이름·설명이 곧 프롬프트" | `description`을 바꾸면 모델이 도구를 고르는 방식이 바뀐다 (도전 과제로 직접 바꿔서 실험해볼 수 있다) |

다음 장(멀티 에이전트 설계)에서는 Claude Code가 작업을 혼자 다 하지 않고, 다른
에이전트에게 작업을 나눠 맡기는 걸 직접 시켜보고 그 결과를 들여다본다.
