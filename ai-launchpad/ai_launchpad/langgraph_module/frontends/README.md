# Frontends — LangGraph 에이전트 웹 UI

LangGraph Server API를 통해 에이전트와 대화하는 Streamlit 웹 UI입니다.

## 전체 구조

```
브라우저 (Streamlit UI)
    ↓ REST API
LangGraph Server (localhost:2024)
    ↓ 에이전트 로드
frontends/agents/
    ├─ researcher.py   → Researcher 에이전트 (웹 검색)  ── gemma-4-31b-it
    └─ planner.py      → Planner 에이전트 (태스크 관리) ── gemma-4-31b-it
```

## 파일별 역할

| 파일 | 역할 |
|---|---|
| `agents/researcher.py` | 웹 검색 에이전트 — LangGraph Server에 로드됨 |
| `agents/planner.py` | 태스크 관리 에이전트 — LangGraph Server에 로드됨 |
| `streamlit_ui/app.py` | Streamlit 채팅 UI — 에이전트 선택, 대화 관리, 스트리밍 표시 |
| `streamlit_ui/api.py` | LangGraph Server API 클라이언트 — SDK 래핑 |

## 실행 방법

### 1단계: LangGraph Server 실행

```bash
cd ai_launchpad/langgraph_module/langgraph_server
langgraph dev
```

→ `http://localhost:2024` 에서 서버 시작
→ `http://localhost:2024/docs` 에서 API 문서 확인 가능

### 2단계: Streamlit UI 실행

```bash
cd ai_launchpad/langgraph_module/frontends/streamlit_ui
streamlit run app.py
```

→ `http://localhost:8501` 에서 웹 UI 접속

## 필요한 API 키

```
GOOGLE_API_KEY=...    # Gemma 모델 (Google AI)
TAVILY_API_KEY=...    # 웹 검색 (Researcher 에이전트)
```

## 에이전트별 기능

### Researcher (웹 검색 에이전트)
- `search_web`: Tavily로 웹 검색, 제목/URL/요약 반환
- `extract_content_from_webpage`: URL에서 전체 본문 추출
- 예시: "AI 에이전트의 최신 트렌드를 검색해줘"

### Planner (태스크 관리 에이전트)
- `generate_task_list`: 태스크 목록 생성 또는 교체
- `view_task_list`: 현재 태스크 목록 조회
- 예시: "이번 주 할 일 목록 만들어줘"

## 핵심 개념

### LangGraph Server & SDK
```python
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://localhost:2024")

# 에이전트 목록 조회
assistants = client.assistants.search()

# 스트리밍 실행
for chunk in client.runs.stream(thread_id=..., assistant_id=..., input=...):
    if chunk.event == "messages":
        yield chunk.data[0]["content"]
```

### Thread (대화 세션)
- 각 대화는 독립된 Thread로 관리됩니다
- `user_id` 메타데이터로 사용자별 대화를 구분합니다
- LangGraph Server가 Thread별 상태(메시지 히스토리)를 자동 저장합니다

### 새 에이전트 추가 방법
1. `agents/` 폴더에 에이전트 파일 생성 (`graph` 변수 export 필수)
2. `langgraph_server/langgraph.json`에 등록:
   ```json
   {
     "graphs": {
       "MyAgent": "../agents/my_agent.py:graph"
     }
   }
   ```
3. `langgraph dev` 재시작

## 참고 자료

- [LangGraph Server 문서](https://docs.langchain.com/langgraph-platform/langgraph-server)
- [LangGraph SDK (Python)](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)
- [Streamlit 문서](https://docs.streamlit.io/)
