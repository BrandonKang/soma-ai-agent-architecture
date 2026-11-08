# 2장 실습 — "모델은 컨텍스트에 있는 것만 안다"

1장과 같은 방식이다: 가짜 모델이 아니라 **지금 쓰고 있는 진짜 Claude Code**로 실험한다.
이번엔 **완전히 똑같은 요청을 두 번** 시킨다. 차이는 단 하나 — 두 번째에는
`CLAUDE.md`(프로젝트 지침 파일) 한 장을 추가해둔다는 것뿐이다.

- 똑같은 요청인데 결과가 달라진다면? → "모델이 컨텍스트에 있는 걸 실제로 읽고 쓴다"는 증거
- 턴이 지날수록 숫자(토큰)가 커지는 걸 직접 본다면? → "컨텍스트 창이 누적된다"는 슬라이드 문장이
  추상적 비유가 아니라는 증거

---

## 0. 폴더 구조

```
ch2_live_context_engineering/
├── sample_repo/
│   ├── src/utils/formatting.py   # 기존 유틸 함수 2개 (날짜, 퍼센트)
│   └── tests/test_formatting.py  # 기존 함수 테스트
├── CLAUDE.md.example              # 2단계에서 복사해 쓸 프로젝트 지침 템플릿
├── trace_session.py               # ★ 세션을 턴 표 + 컨텍스트 크기로 보여주는 도구 (1장 버전 확장판)
└── reset.py                       # 실습을 다시 처음부터 하려면 실행
```

---

## 1. 기존 상태 확인

```bash
cd ch2_live_context_engineering/sample_repo
python3 tests/test_formatting.py
```

`전체 통과`가 떠야 정상이다. `src/utils/formatting.py`에는 `format_date`, `format_percentage`
두 함수만 있다. 이 레포에는 아직 `CLAUDE.md`가 없다.

---

## 2. 1라운드 — 아무 지침 없이 요청하기

`sample_repo` 안에서 Claude Code를 실행한다.

```bash
claude
```

이렇게 요청한다.

```
src/utils 안에 금액(정수)을 '12,000원' 형식의 문자열로 포맷하는 함수를 추가해줘
```

끝나면 결과를 확인한다.

```bash
find src -type f
cat src/utils/formatting.py
```

**실제로 내가 돌렸을 때**: 새 함수(`format_currency`)가 **기존 `formatting.py` 파일 안에**
추가됐다. 아주 자연스러운 선택이다 — 모델 입장에선 "유틸 함수는 formatting.py에 모아둔다"는
게 이 레포에서 유일하게 보이는 패턴이기 때문이다.

---

## 3. 초기화 후 2라운드 — 이번엔 지침을 하나 준다

```bash
python3 ../reset.py
```

`CLAUDE.md.example`의 내용을 `sample_repo/CLAUDE.md`로 복사한다.

```bash
cp ../CLAUDE.md.example CLAUDE.md
cat CLAUDE.md
```

내용은 이렇다.

```markdown
# 프로젝트 규칙

- 새로운 유틸리티 함수를 추가할 때는 반드시 카테고리별로 별도 파일을 새로 만든다.
  - 예: 통화(화폐) 관련 함수는 `src/utils/currency.py`
  - 예: 날짜 관련 함수는 `src/utils/date.py`
- 기존 파일 `src/utils/formatting.py`에는 더 이상 새 함수를 추가하지 않는다 (레거시, 점진적으로 이전 중).
```

이제 **새 Claude Code 세션**을 열고, **1라운드와 완전히 똑같은 문장**을 그대로 입력한다.

```bash
claude
```

```
src/utils 안에 금액(정수)을 '12,000원' 형식의 문자열로 포맷하는 함수를 추가해줘
```

끝나면 다시 확인한다.

```bash
find src -type f
cat src/utils/formatting.py   # 그대로여야 한다
cat src/utils/currency.py     # 새로 생겼어야 한다
```

**실제로 내가 돌렸을 때**: 이번엔 `formatting.py`는 전혀 건드리지 않고, `src/utils/currency.py`를
새로 만들어 그 안에 함수를 추가했다. 심지어 작업 중 모델이 남긴 메시지에 이렇게 적혀 있었다.

> "CLAUDE.md 규칙에 따라 `formatting.py`에 추가하지 않고 새 파일 `src/utils/currency.py`를
> 생성합니다."

**똑같은 한 문장을 시켰는데 결과가 완전히 달라졌다.** 바뀐 건 `CLAUDE.md` 파일 하나가
폴더에 있었다는 것뿐이다. 슬라이드의 "컨텍스트 창에 들어가는 것들" 표에서 "프로젝트 지침
(CLAUDE.md 등) — 고정"이 실제로 매 턴 모델에게 보여지고 있었다는 뜻이다.

---

## 4. trace_session.py로 두 라운드 비교하기

```bash
python3 ../trace_session.py --list
```

방금 두 세션(1라운드, 2라운드)의 id를 확인하고 각각 돌려본다.

```bash
python3 ../trace_session.py <1라운드 세션id 일부>
python3 ../trace_session.py <2라운드 세션id 일부>
```

### 실제로 내가 받은 결과 (요약)

**1라운드 (CLAUDE.md 없음)**

```
[턴 1] 모델 호출 1회  [이 시점 컨텍스트 ≈ 28,772 토큰]
        -> 도구 호출: Bash(ls -la src/utils ...)
[턴 2] 모델 호출 1회  [이 시점 컨텍스트 ≈ 29,098 토큰]
        -> 도구 호출: Read(.../formatting.py)
[턴 3] 모델 호출 1회  [이 시점 컨텍스트 ≈ 29,453 토큰]
        -> 텍스트: 기존 스타일에 맞춰 같은 파일에 함수를 추가하겠습니다.
        -> 도구 호출: Edit(formatting.py에 format_currency 추가)
[턴 4] 모델 호출 1회  [이 시점 컨텍스트 ≈ 29,989 토큰]
        -> 텍스트: `format_currency` 함수를 `src/utils/formatting.py`에 추가했습니다...
```

**2라운드 (CLAUDE.md 있음)**

```
[턴 1] 모델 호출 1회  [이 시점 컨텍스트 ≈ 29,111 토큰]
        -> 도구 호출: Bash(ls -la ...)
[턴 2] 모델 호출 1회  [이 시점 컨텍스트 ≈ 29,709 토큰]
        -> 도구 호출: Bash(find ... -name "*.py")
[턴 3] 모델 호출 1회  [이 시점 컨텍스트 ≈ 29,955 토큰]
        -> 텍스트: CLAUDE.md 규칙에 따라 formatting.py에 추가하지 않고 새 파일 currency.py를 생성합니다.
        -> 도구 호출: Write(src/utils/currency.py)
[턴 4] 모델 호출 1회  [이 시점 컨텍스트 ≈ 30,354 토큰]
        -> 텍스트: `src/utils/currency.py`에 `format_won` 함수를 추가했습니다...
```

**관찰 포인트 — 직접 숫자를 짚어보자:**

1. **턴마다 컨텍스트 크기가 계속 커진다** (28,772 → 29,098 → 29,453 → 29,989). 슬라이드의
   "도구 결과: 파일 내용·명령 출력 — 빠르게 증가"가 숫자로 보인다. Read/Bash 결과가
   `messages`에 쌓일 때마다 다음 호출의 입력 토큰이 늘어난다.
2. **2라운드의 턴 1이 1라운드의 턴 1보다 이미 더 크다** (29,111 vs 28,772). 아직 아무 도구도
   호출하기 전인데 벌써 차이가 난다 — `CLAUDE.md` 내용 자체가 "고정 컨텍스트"로 맨 처음부터
   얹혀서 시작하기 때문이다.
3. **1라운드 턴 2, 2라운드 턴 1~2는 "탐색"이다.** Read든 Bash find든, 전체 저장소를 통째로
   컨텍스트에 넣는 게 아니라 필요한 부분만 그때그때 가져온다 — 슬라이드의
   "Just-in-time: 필요할 때만 읽기"가 바로 이것이다.

---

## 5. 원본 로그에서 "토큰이 쌓이는 증거" 직접 찾기 (심화)

`trace_session.py`가 계산해준 숫자가 어디서 나왔는지 원본에서 확인한다.

```bash
python3 ../trace_session.py --list
python3 -c "
import json, sys
for line in open(sys.argv[1]):
    rec = json.loads(line)
    if rec.get('type') == 'assistant':
        usage = rec.get('message', {}).get('usage')
        if usage:
            print({k: usage[k] for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')})
" "<--list에서 확인한 .jsonl 전체 경로>"
```

`cache_read_input_tokens` 값이 턴을 거듭할수록 커지는 걸 직접 본다. 이건 슬라이드 5장에서
배울 "프롬프트 캐싱"과도 연결된다 — 이미 본 적 있는 컨텍스트(시스템 프롬프트, CLAUDE.md,
이전 대화)는 매번 새로 계산하지 않고 캐시에서 읽어온다. 그래서 컨텍스트가 커져도 비용이
선형적으로만 늘지, 매번 처음부터 다시 계산하는 것보다는 저렴하다.

---

## 6. 다시 처음부터

```bash
python3 reset.py
```

`formatting.py` 복원, `currency.py`/`CLAUDE.md` 삭제까지 한 번에 처리한다.

---

## 7. 도전 과제

### 도전 1 — Just-in-time의 반대: 다 퍼먹여보기
`reset.py` 실행 후, 이번엔 요청할 때 파일 내용을 통째로 프롬프트에 붙여넣어보자.

```bash
cat src/utils/formatting.py
```

출력된 내용을 복사해서 이렇게 요청해본다.

```
여기 src/utils/formatting.py 전체야: <붙여넣기>
이 파일에 금액을 '12,000원'으로 포맷하는 함수를 추가해줘
```

`trace_session.py`로 턴 수와 턴 1의 컨텍스트 크기를 2절(그냥 요청만 한 경우)과 비교해보자.
도구 호출(Read)이 줄었는가? 그런데 턴 1 시작 컨텍스트는 오히려 더 큰가, 비슷한가?
"누가 읽어오느냐(에이전트가 필요한 만큼 vs 사용자가 통째로)"가 왜 턴 수와 컨텍스트 구성에
차이를 만드는지 설명해보자.

### 도전 2 — Isolation 체감: 탐색을 서브에이전트에게 맡기기
새 세션에서 이렇게 명시적으로 요청해본다.

```
sample_repo 전체 구조를 서브에이전트에게 맡겨서 파악하게 하고, 요약만 받아서 알려줘
```

`trace_session.py` 결과에서 탐색용 도구 호출들이 메인 턴 표에 그대로 다 나오는지, 아니면
"서브에이전트에게 위임함"에 해당하는 도구 호출 한 번과 그 요약 결과만 보이는지 확인해보자.
후자라면, 슬라이드의 "Isolation: 탐색은 별도 컨텍스트에서 하고 요약만 주 에이전트에 돌려준다"가
메인 세션의 컨텍스트 크기를 어떻게 아껴주는지 설명해보자.

### 도전 3 — Memory 체감: 세션이 끊겨도 파일로 이어가기
현재 세션에서 이렇게 요청한다.

```
지금까지 뭘 했는지 progress.md 파일에 정리해서 기록해줘
```

파일이 생겼으면 Claude Code 세션을 **완전히 종료**한다 (`/exit` 또는 `Ctrl+D`). 그리고
**새 세션**을 열어 이렇게 요청한다.

```
progress.md를 읽고 이어서 작업해줘
```

`messages`는 완전히 새로 시작됐는데(대화 이력이 없는 새 세션인데도), 모델이 이전 작업
맥락을 알고 있다. `trace_session.py`로 이 새 세션의 턴 1이 무슨 도구를 호출하는지
확인해보자(아마 `progress.md`를 `Read`할 것이다). 이게 슬라이드의 "Memory: 외부 메모리 —
진행 상황과 결정 사항을 파일에 기록해 두고 다시 읽는다"이다.

### 도전 4 — Compaction 살짝 체감하기
한 세션에서 서로 다른 작은 요청을 5번 정도 연달아 시켜 대화를 길게 만들어본다(예: 함수를
하나씩 추가/수정/되돌리기 등). 그다음 세션 안에서 `/compact`를 입력해본다.

`/compact` 전후로 `trace_session.py` 결과가 어떻게 달라지는지 비교해보자. 압축 이후의
첫 턴은 지금까지의 대화를 요약한 형태로 시작하는가? 컨텍스트 크기(토큰)가 압축 직후
줄어드는가? 이것이 슬라이드의 "Compaction: 컨텍스트가 차면 이전 이력을 요약본으로 바꿔
작업을 이어간다"이다.

---

## 8. 정리

| 슬라이드 문장 | 실습에서 확인한 것 |
|---|---|
| "모델은 컨텍스트에 있는 것만 안다" | CLAUDE.md 한 장 차이로 완전히 다른 파일 구조를 만든 것 |
| "프로젝트 지침(CLAUDE.md 등) — 고정" | 2라운드 턴 1이 1라운드 턴 1보다 처음부터 더 컸던 것 |
| "도구 결과 — 빠르게 증가" | 턴이 지날수록 커지는 `cache_read_input_tokens` 숫자 |
| "Just-in-time: 필요할 때만 읽기" | 전체 저장소 대신 `find`/`Read`로 필요한 파일만 가져온 것 |
| "Isolation: 서브에이전트 격리" | 도전 2 — 탐색을 위임하고 요약만 받았을 때 메인 컨텍스트가 덜 자란 것 |
| "Memory: 외부 메모리" | 도전 3 — 새 세션인데도 `progress.md`를 통해 맥락이 이어진 것 |
| "Compaction: 대화 압축" | 도전 4 — `/compact` 전후로 컨텍스트가 줄어든 것 |

다음 장(Tool Calling & MCP)에서는 지금까지 당연하게 지켜봤던 "Bash를 실행해도 될까요?"
승인 요청이 정확히 어떤 원리로 뜨고, 도구를 어떻게 설계해야 모델이 잘 쓰는지를 다룬다.
