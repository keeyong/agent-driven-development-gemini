"""
프롬프트 체이닝 (Prompt Chaining) — 복잡한 작업을 단계별로 분해

복잡한 작업을 여러 단계로 나눠서 각 단계의 출력을 다음 단계의 입력으로 연결하는 패턴입니다.

예제: 블로그 포스트 생성 워크플로우
    outline (아웃라인) → draft (초안) → seo_optimization (SEO 최적화)

## 핵심 개념
1. 작업 분해: 복잡한 작업을 명확한 단계로 나누면 각 단계를 독립적으로 최적화할 수 있습니다.
2. 관심사 분리: 각 노드가 한 가지 작업만 담당하므로 모델 혼선과 환각을 줄입니다.
3. 제어 가능성: 각 단계의 출력을 State에 저장해서 디버깅/검사가 쉽습니다.

## 실행 방법
    uv run python workflows/3_prompt_chaining.py
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Annotated
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, add_messages, END
from langgraph.prebuilt import ToolNode

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)

print("=" * 50)
print("  📌 프롬프트 체이닝: 블로그 작성 워크플로우")
print("  outline → draft → SEO 최적화")
print("=" * 50)


#################################
# State
#################################

# 각 단계의 결과를 별도 필드에 저장 → 디버깅 및 중간 결과 확인 용이
class WorkflowState(BaseModel):
    """블로그 작성 워크플로우 상태"""
    messages: Annotated[list, add_messages] = []
    topic: str = ""        # 사용자 입력 주제
    outline: str = ""      # 1단계: 아웃라인
    draft: str = ""        # 2단계: 초안
    final: str = ""        # 3단계: SEO 최적화 최종본


#################################
# Step 1: 아웃라인 생성
#################################

def generate_outline(state: WorkflowState):
    """주제를 받아 블로그 아웃라인을 생성합니다."""
    print("\n[1단계] 아웃라인 생성 중...")
    system_prompt = SystemMessage(content="""
    You are a blog outline creator. Create a clear, structured outline for a blog post.

    Requirements:
    - Include an introduction, 3 main sections, and a conclusion
    - Each section should have 2-3 bullet points
    - Keep it concise and focused

    Respond with only the outline.
    """)
    response = llm.invoke([system_prompt] + state.messages)
    print(f"✅ 아웃라인 생성 완료 ({len(response.content)}자)")
    return {"outline": response.content, "messages": [response]}


#################################
# Step 2: 초안 작성
#################################

def generate_draft(state: WorkflowState):
    """아웃라인을 바탕으로 블로그 초안을 작성합니다."""
    print("\n[2단계] 초안 작성 중...")
    system_prompt = SystemMessage(content=f"""
    You are a blog writer. Write a complete blog post draft based on this outline:

    <Outline>
    {state.outline}
    </Outline>

    Requirements:
    - 600-800 words
    - Engaging and informative tone
    - Practical examples where relevant

    Respond with only the draft.
    """)
    response = llm.invoke([system_prompt] + state.messages)
    print(f"✅ 초안 작성 완료 ({len(response.content)}자)")
    return {"draft": response.content, "messages": [response]}


#################################
# Step 3: SEO 최적화
#################################

def seo_optimization(state: WorkflowState):
    """초안을 SEO에 최적화된 최종본으로 다듬습니다."""
    print("\n[3단계] SEO 최적화 중...")
    system_prompt = SystemMessage(content=f"""
    You are an SEO expert. Optimize this blog post draft for search engines.

    <Draft>
    {state.draft}
    </Draft>

    Requirements:
    - Add a compelling meta description (150-160 chars)
    - Add 5 relevant SEO keywords at the top
    - Optimize headings with keywords
    - Keep the original content intact

    Respond with the optimized post.
    """)
    response = llm.invoke([system_prompt] + state.messages)
    print(f"✅ SEO 최적화 완료 ({len(response.content)}자)")
    return {"final": response.content, "messages": [response]}


#################################
# 그래프 구성
#################################

# 노드를 순서대로 연결: outline → draft → seo → END
builder = StateGraph(WorkflowState)

builder.add_node(generate_outline)
builder.add_node(generate_draft)
builder.add_node(seo_optimization)

builder.set_entry_point("generate_outline")
builder.add_edge("generate_outline", "generate_draft")
builder.add_edge("generate_draft", "seo_optimization")
builder.add_edge("seo_optimization", END)

graph = builder.compile()

# 실행
topic = "Why MCP (Model Context Protocol) is changing how AI agents work"
print(f"\n주제: {topic}")

response = graph.invoke(WorkflowState(
    messages=[topic],
    topic=topic,
))

print("\n" + "=" * 50)
print("  📄 최종 결과")
print("=" * 50)
print(f"\n[아웃라인]\n{response['outline']}")
print(f"\n[최종본 (SEO 최적화)]\n{response['final']}")
