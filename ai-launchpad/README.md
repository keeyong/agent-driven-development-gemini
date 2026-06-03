# AI Launchpad

AI 에이전트 구축을 위한 튜토리얼, 코드 템플릿, 예제 모음입니다.
Google Gemma/Gemini 모델 기반으로 구성되어 있습니다.

---

## 시작하기

### 1. uv 설치

[uv](https://docs.astral.sh/uv/)는 pip, poetry, pyenv를 대체하는 Python 패키지 매니저입니다.

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 저장소 클론 및 의존성 설치

```bash
git clone https://github.com/kenneth-liao/ai-launchpad.git
cd ai-launchpad
uv sync
```

`uv sync`는 `.venv/` 가상환경을 자동 생성하고 모든 의존성을 설치합니다.

### 3. API 키 설정

프로젝트 루트에 `.env` 파일을 생성하고 API 키를 추가합니다:

```env
GOOGLE_API_KEY=...       # 필수 — Gemma/Gemini 모델 (Google AI Studio)
TAVILY_API_KEY=...       # 필수 — 웹 검색 (Researcher 에이전트)
LANGSMITH_API_KEY=...    # 선택 — LangGraph 관찰성/디버깅
```

| API 키 | 발급처 | 용도 |
|---|---|---|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | 모든 LLM 호출 |
| `TAVILY_API_KEY` | [Tavily](https://tavily.com/) | 웹 검색 도구 |
| `LANGSMITH_API_KEY` | [LangSmith](https://smith.langchain.com/) | 에이전트 트레이싱 (선택) |

### 4. 실행

```bash
# 예시: agent_from_scratch 첫 번째 파일 실행
uv run python ai_launchpad/agents_module/agent_from_scratch/1_llms.py
```

---

## 프로젝트 구조

```
ai-launchpad/
├── pyproject.toml
└── ai_launchpad/
    ├── agents_module/          # 에이전트 기초 (Google Gemma 4 31B)
    │   ├── agent_from_scratch/ # LLM → 도구 → 검색 → 메모리 → 에이전트
    │   └── agent_with_mcp/     # MCP 서버 연동 에이전트
    └── langgraph_module/       # LangGraph 기반 에이전트 (Gemma 4 31B)
        ├── effective_agents/   # 워크플로우 패턴 1~8
        ├── multi_agent/        # 멀티 에이전트 (Supervisor 패턴)
        ├── frontends/          # Streamlit UI + LangGraph Server 에이전트
        └── langgraph_server/   # LangGraph Server 설정 (langgraph.json)
```

---

## 모듈별 실행 방법

### agents_module

```bash
# 1. LLM 기초 + 구조화 출력
uv run python ai_launchpad/agents_module/agent_from_scratch/1_llms.py

# 2. 도구 호출 (웹 검색 포함)
uv run python ai_launchpad/agents_module/agent_from_scratch/2_tool_calling.py

# 3. 벡터 검색 (ChromaDB + Google Embedding)
uv run python ai_launchpad/agents_module/agent_from_scratch/3_retrieval.py

# 4. 장기 메모리
uv run python ai_launchpad/agents_module/agent_from_scratch/4_long_term_memory.py

# 5. 단기 메모리
uv run python ai_launchpad/agents_module/agent_from_scratch/5_short_term_memory.py

# 6. 완성된 에이전트 (MCP 없이)
uv run python ai_launchpad/agents_module/agent_from_scratch/6_agent.py

# MCP 에이전트 (별도 터미널에서 MCP 서버 먼저 실행)
uv run python ai_launchpad/agents_module/agent_with_mcp/tools/retrieval_mcp.py
uv run python ai_launchpad/agents_module/agent_with_mcp/main.py
```

### langgraph_module — effective_agents

```bash
uv run python ai_launchpad/langgraph_module/effective_agents/building_blocks/1_llm.py
uv run python ai_launchpad/langgraph_module/effective_agents/building_blocks/2_augmented_llm.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/3_prompt_chaining.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/4_routing.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/5_parallelization.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/6_orchestrator-workers.py
uv run python ai_launchpad/langgraph_module/effective_agents/workflows/7_evaluator-optimizer.py
uv run python ai_launchpad/langgraph_module/effective_agents/agents/8_agent.py
```

### langgraph_module — multi_agent

```bash
uv run python -m ai_launchpad.langgraph_module.multi_agent.supervisor.main
```

### langgraph_module — frontends (LangGraph Server + Streamlit)

```bash
# 터미널 1: LangGraph Server 실행
cd ai_launchpad/langgraph_module/langgraph_server
langgraph dev

# 터미널 2: Streamlit UI 실행
cd ai_launchpad/langgraph_module/frontends/streamlit_ui
streamlit run app.py
```

---

## 사용 모델

| 모듈 | 모델 | 용도 |
|---|---|---|
| `agents_module` | `gemma-4-31b-it` | LLM, 도구 호출, 에이전트 |
| `effective_agents` | `gemma-4-31b-it` | 워크플로우, 에이전트 |
| `multi_agent/supervisor` | `gemma-4-31b-it` | 멀티 에이전트 조율 |
| `frontends/agents` | `gemma-4-31b-it` | Researcher, Planner |
| 임베딩 | `models/gemini-embedding-001` | ChromaDB 벡터 검색 |

---

## 참고 자료

- [Google AI Studio](https://aistudio.google.com/) — API 키 발급
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [LangGraph Server](https://docs.langchain.com/langgraph-platform/langgraph-server)
- [FastMCP 문서](https://gofastmcp.com/)
- [uv 문서](https://docs.astral.sh/uv/)
