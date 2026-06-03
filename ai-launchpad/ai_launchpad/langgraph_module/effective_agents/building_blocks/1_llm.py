"""
LLM 기초 — LangGraph의 출발점

LLM은 에이전트의 두뇌입니다. 하지만 기본 LLM 하나만으로는 에이전트가 될 수 없습니다.
이 파일은 LLM의 가장 중요한 특성인 'stateless(무상태)'를 이해하는 것이 목표입니다.

## 핵심 개념
1. LLM은 stateless — 매 API 호출은 독립적이며 이전 대화를 기억하지 않습니다.
2. LLM → 에이전트로 발전하려면 3가지가 필요합니다:
   - 메모리 (Memory): 대화 히스토리 유지
   - 도구 (Tools): 환경에 작용할 수 있는 능력
   - 자율성 (Agency): 다음 행동을 스스로 결정하는 능력

## 실행 방법
    uv run python building_blocks/1_llm.py
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# LangChain의 Google Gemini 통합 — ChatOpenAI와 동일한 인터페이스를 사용하므로
# LangGraph 코드를 거의 수정 없이 모델만 바꿀 수 있음
llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)

print("=" * 50)
print("  📌 LLM 기초: Stateless 특성 이해")
print("=" * 50)


#################################
# LLM은 Stateless (무상태)
#################################

print("\n[1단계] 자기소개 후 이름 물어보기")
print("-" * 40)

# 처음 대화: 이름을 알려줌
response = llm.invoke("Hello! I'm Keeyong.")
print(f"LLM 응답: {response.content}")

# 두 번째 대화: 이름을 기억하는지 확인
# → LLM은 stateless이므로 이전 대화를 기억하지 못함
response = llm.invoke("What's my name?")
print(f"\nLLM 응답 (이름 질문): {response.content}")
print("\n⚠️  LLM이 이름을 모릅니다 — 각 호출은 독립적인 API 요청이기 때문입니다.")
print("   이전 대화 내용을 전달하지 않으면 LLM은 아무것도 기억하지 못합니다.")
