# Building Effective Agents with LangGraph

Anthropic의 [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) 가이드를 LangGraph로 구현한 튜토리얼입니다.
핵심 설계 패턴을 이해하면 거의 모든 AI 문제를 해결할 수 있습니다.

## 사용 모델

모든 파일은 **Google Gemini** (`gemini-2.5-flash`)를 사용합니다.
`GOOGLE_API_KEY`를 `.env` 파일에 설정하세요.

## 파일별 요약

| 파일 | 패턴 | 핵심 내용 | 실행 시간 |
|---|---|---|---|
| `building_blocks/1_llm.py` | LLM 기초 | LLM의 stateless 특성 이해 | ~5초 |
| `building_blocks/2_augmented_llm.py` | 증강 LLM | 메모리(MemorySaver) + 도구(ToolNode) 추가 | ~15초 |
| `workflows/3_prompt_chaining.py` | 프롬프트 체이닝 | outline → draft → SEO (블로그 생성) | ~30초 |
| `workflows/4_routing.py` | 라우팅 | 요청 분류 후 LinkedIn/Instagram/Blog로 분기 | ~20초 |
| `workflows/5_parallelization.py` | 병렬화 | 포스트+이미지+해시태그 동시 생성 | ~30초 |
| `workflows/6_orchestrator-workers.py` | 오케스트레이터-워커 | 딥 리서치 (동적 태스크 분배 + 병렬 검색) | ~60초 |
| `workflows/7_evaluator-optimizer.py` | 평가자-최적화기 | 코드 생성 + 반복 품질 개선 루프 | ~30초 |
| `agents/8_agent.py` | 완전한 에이전트 | LinkedIn 콘텐츠 크리에이터 (자율 계획 + 도구) | 대화형 |

## 실행 방법

프로젝트 루트(`ai-launchpad/`)에서 실행하세요:

```bash
# Building Blocks
uv run python ai_launchpad/langgraph_module/effective_agents/building_blocks/1_llm.py
uv run python ai_launchpad/langgraph_module/effective_agents/building_blocks/2_augmented_llm.py

# Workflows
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/3_prompt_chaining.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/4_routing.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/5_parallelization.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/6_orchestrator-workers.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/7_evaluator-optimizer.py

# Agent (대화형)
uv run python ai_launchpad/langgraph_module/effective_agents/agents/8_agent.py
```

## 핵심 개념 요약

### LangGraph 기본 구조
```python
from langgraph.graph import StateGraph, END

builder = StateGraph(MyState)
builder.add_node("node_name", my_function)
builder.set_entry_point("node_name")
builder.add_edge("node_name", END)
graph = builder.compile()

graph.invoke(MyState(messages=["hello"]))
```

### 패턴별 특징

| 패턴 | 언제 사용 | LangGraph 핵심 |
|---|---|---|
| 프롬프트 체이닝 | 단계가 명확히 정해진 복잡한 작업 | `add_edge` (순차 연결) |
| 라우팅 | 입력에 따라 다른 처리가 필요할 때 | `add_conditional_edges` |
| 병렬화 | 독립적인 작업을 동시에 처리할 때 | 여러 `add_edge(START, ...)` |
| 오케스트레이터-워커 | 태스크 수를 미리 알 수 없을 때 | `Send` API |
| 평가자-최적화기 | 반복 개선으로 품질을 높일 때 | 조건부 루프 |
| 에이전트 | 단계를 미리 알 수 없는 자율적 작업 | `MemorySaver` + `ToolNode` |

### 워크플로우 vs 에이전트

```
워크플로우: 단계가 명확 → 더 안정적, 최적화 쉬움
에이전트:   단계가 불명확 → 더 유연, 예측 어려움

→ 항상 가장 단순한 해결책부터 시작하세요
```

## 필요한 API 키

| 파일 | 필요한 키 |
|---|---|
| 1~5번 | `GOOGLE_API_KEY` |
| 6번 | `GOOGLE_API_KEY`, `TAVILY_API_KEY` |
| 7번 | `GOOGLE_API_KEY` |
| 8번 | `GOOGLE_API_KEY`, `TAVILY_API_KEY` |

## 참고 자료

- [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [Google Gemini API](https://ai.google.dev/)
