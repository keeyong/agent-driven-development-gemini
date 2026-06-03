# Multi-Agent Supervisor

Supervisor 패턴으로 구현한 멀티 에이전트 시스템입니다.
Supervisor가 Researcher와 Copywriter 서브에이전트를 조율해서 LinkedIn/블로그 콘텐츠를 생성합니다.

## 전체 구조

```
사용자
  ↓
Supervisor (조율자) ── gemma-4-31b-it
  │
  ├─→ call_researcher → Researcher 서브그래프 ── gemma-4-31b-it
  │     ├─ search_web              (Tavily 웹 검색)
  │     ├─ extract_content_from_webpage  (웹페이지 본문 추출)
  │     └─ generate_research_report     (보고서 생성 → research_reports에 저장)
  │
  ├─→ call_researcher (필요 시 반복 — 토픽별로 여러 번)
  │
  └─→ call_copywriter → Copywriter 서브그래프 ── gemma-4-31b-it
        ├─ review_research_reports  (보고서 조회)
        ├─ generate_linkedin_post   (LinkedIn 포스트 → ai_files/ 저장)
        └─ generate_blog_post       (블로그 포스트 → ai_files/ 저장)
```

## 파일별 역할

| 파일 | 역할 |
|---|---|
| `main.py` | 실행 진입점 — Rich 터미널 UI로 스트리밍 출력 |
| `supervisor.py` | 부모 그래프 — 사용자와 대화, 서브에이전트에 작업 위임 |
| `researcher.py` | 서브그래프 1 — 웹 검색 + 리서치 보고서 생성 |
| `copywriter.py` | 서브그래프 2 — 보고서 기반 콘텐츠(LinkedIn/블로그) 작성 |
| `prompts/` | 각 에이전트의 시스템 프롬프트 |
| `example_content/` | 카피라이터 참고용 우수 콘텐츠 예시 |
| `ai_files/` | 생성된 콘텐츠 저장 폴더 (자동 생성) |

## 실행 방법

프로젝트 루트(`ai-launchpad/`)에서 실행:

```bash
uv run python -m ai_launchpad.langgraph_module.multi_agent.supervisor.main
```

또는 supervisor 폴더에서 직접:

```bash
cd ai_launchpad/langgraph_module/multi_agent/supervisor
uv run python main.py
```

## 필요한 API 키

```
GOOGLE_API_KEY=...    # Gemma 모델 (Google AI)
TAVILY_API_KEY=...    # 웹 검색 (Researcher 에이전트)
```

## 예시 요청

```
Write a LinkedIn post about how AI agents are changing the way we work

Write a blog post about the top AI tools for entrepreneurs with real-world
examples and case studies. Include actual numbers and results.

Write a LinkedIn post on how MCP (Model Context Protocol) is unlocking
new possibilities for AI agents. Include practical examples.
```

## 핵심 개념

### 서브그래프 (Subgraph)
각 에이전트(researcher, copywriter)가 독립적인 LangGraph 그래프로 구현됩니다.
서브그래프는 **checkpointer 없이** 컴파일하고, 부모(supervisor)의 checkpointer를 상속합니다.

```python
# 서브그래프 — checkpointer 없이 컴파일
graph = builder.compile()

# 부모 그래프 — checkpointer 설정 (서브그래프가 상속)
graph = builder.compile(checkpointer=MemorySaver())
```

### 공유 상태 (Shared State)
`research_reports` 필드를 supervisor ↔ researcher ↔ copywriter가 공유합니다.
필드명과 리듀서(`operator.add`)가 동일해야 LangGraph가 서브그래프 결과를 부모 상태에 자동 병합합니다.

```python
# 세 State 클래스 모두 동일한 필드 선언
research_reports: Annotated[list, operator.add] = []
```

### Command 프리미티브
도구 내부에서 **상태 업데이트 + 다음 노드 지정**을 동시에 처리합니다.
일반 ToolNode는 항상 호출한 노드로 돌아가지만, Command를 쓰면 원하는 노드로 직접 점프합니다.

```python
# handoff_to_subagent 도구 내부
return Command(
    goto="call_researcher",   # 다음으로 이동할 노드
    update={"task_description": task_description, ...}
)
```

### 에이전트 역할 분리
Supervisor는 태스크 설명만 서브에이전트에 전달합니다 (전체 대화 히스토리 X).
각 에이전트가 자신의 역할에만 집중하므로 컨텍스트가 오염되지 않습니다.

```python
# supervisor → researcher: 태스크 설명만 전달
research_response = await research_agent.ainvoke(
    input={"messages": [HumanMessage(content=state.task_description)]},
)
```

## 주의사항

### Rate Limit (429 오류)
멀티 에이전트는 Supervisor + Researcher + Copywriter가 연속으로 API를 호출하므로
단일 에이전트 대비 훨씬 빠르게 무료 티어 한도에 도달합니다.

- `gemma-4-31b-it` 무료 티어: 분당 30회 요청
- 429 오류 발생 시 1분 기다렸다가 재시도하면 됩니다

### 생성된 파일 위치
콘텐츠는 `ai_files/` 디렉토리에 마크다운 파일로 저장됩니다 (자동 생성).

## 참고 자료

- [LangGraph 서브그래프 문서](https://langchain-ai.github.io/langgraph/concepts/subgraphs/)
- [LangGraph Command 프리미티브](https://langchain-ai.github.io/langgraph/concepts/low_level/#command)
- [langgraph-supervisor-py](https://github.com/langchain-ai/langgraph-supervisor-py) — 고수준 Supervisor 라이브러리
