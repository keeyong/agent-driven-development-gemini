# Multi-Agent AI Applications

## 언제 무엇을 써야 할까?

AI 시스템을 만들기 전에 가장 단순한 해결책부터 고려해야 합니다.

```
워크플로우 (3~7번)  →  단일 에이전트 (8번)  →  멀티 에이전트 (이 폴더)
     ↑ 가장 단순                                      ↑ 가장 복잡
```

### 선택 기준

| 패턴 | 언제 사용 | 특징 |
|---|---|---|
| **AI 워크플로우** | 단계가 명확히 정해진 문제 | 빠르고, 디버그 쉽고, 안정적 |
| **단일 에이전트** | 단계를 미리 알 수 없는 열린 문제 | 유연하지만 예측 어려움 |
| **멀티 에이전트** | 단일 에이전트로 성능이 병목될 만큼 복잡한 문제 | 강력하지만 복잡하고 비용 높음 |

> ⚠️  Gartner: "40% 이상의 에이전트 AI 프로젝트가 2027년까지 비용과 불명확한 비즈니스 가치로 인해 중단될 것"  
> ⚠️  Anthropic: "멀티 에이전트는 단순 채팅 대비 약 15배 더 많은 토큰 사용"

**결론: 항상 가장 단순한 해결책부터 시작하세요.**

---

## 멀티 에이전트의 장점

복잡한 문제에서 멀티 에이전트가 빛을 발하는 이유:

### 1. 병렬화로 효율 향상
여러 에이전트가 동시에 다른 각도에서 작업 → 전체 처리 시간 단축

### 2. 컨텍스트 분리
각 에이전트가 자신의 역할에만 집중 → 컨텍스트 오염 없이 더 높은 품질

### 3. 토큰 스케일링 = 성능 스케일링
에이전트 수 × 컨텍스트 윈도우 = 총 처리 가능 정보량 증가

### 4. 모듈화 및 재사용
각 에이전트를 독립적으로 최적화하고 여러 앱에서 재사용 가능

---

## 이 폴더의 구현

### supervisor/
Supervisor 패턴 구현 — 가장 일반적인 멀티 에이전트 패턴

```
Supervisor (조율자)
├─→ Researcher (웹 검색 + 보고서 생성)
└─→ Copywriter (보고서 기반 콘텐츠 작성)
```

**실행 방법**:
```bash
# 프로젝트 루트에서
uv run python -m ai_launchpad.langgraph_module.multi_agent.supervisor.main
```

**필요한 API 키**: `GOOGLE_API_KEY`, `TAVILY_API_KEY`

---

## 멀티 에이전트 4가지 패턴

| 패턴 | 설명 | 이 폴더 |
|---|---|---|
| **Supervisor** | 상위 에이전트가 하위 에이전트들을 조율 | ✅ supervisor/ |
| **Network** | 에이전트들이 피어-투-피어로 상호작용 | - |
| **Hierarchical** | 트리 구조로 에이전트 계층화 | - |
| **Custom** | 완전히 커스텀한 연결 구조 | - |

---

## 참고 자료

- [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system) ← 필독
- [LangGraph Multi-Agent 패턴](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
- [State of AI Agents (LangChain)](https://www.langchain.com/stateofaiagents)
- [langgraph-supervisor-py](https://github.com/langchain-ai/langgraph-supervisor-py) — 고수준 Supervisor 라이브러리
