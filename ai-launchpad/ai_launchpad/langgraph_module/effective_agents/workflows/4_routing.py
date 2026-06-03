"""
라우팅 (Routing) — 조건에 따라 다른 워크플로우로 분기

사용자 요청을 분류하고 해당하는 전문 워크플로우로 연결하는 패턴입니다.

예제: 콘텐츠 생성 워크플로우
    사용자 요청 → 분류 (linkedin/instagram/blog) → 각 플랫폼별 전문 생성기

LinkedIn 플로우에는 추가로 검토(review) → 재작성(rewrite) 루프가 포함됩니다.

## 핵심 개념
1. 관심사 분리: 플랫폼별 요구사항이 다르므로 각자 독립적인 워크플로우를 가집니다.
2. 모듈성: 새 플랫폼 추가 시 노드와 엣지만 추가하면 됩니다.
3. conditional_edges: 상태나 조건에 따라 다음 노드를 동적으로 결정합니다.
4. with_structured_output: LLM 출력을 Pydantic 모델로 강제해서 신뢰성을 높입니다.

## 실행 방법
    uv run python workflows/4_routing.py
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, add_messages, END, START

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)

print("=" * 50)
print("  📌 라우팅: 플랫폼별 콘텐츠 생성")
print("  LinkedIn / Instagram / Blog")
print("=" * 50)


#################################
# State
#################################

class WorkflowState(BaseModel):
    """콘텐츠 생성 워크플로우 상태"""
    messages: Annotated[list, add_messages] = []
    content: str | None = None   # 생성된 콘텐츠
    rewrite: bool = False         # LinkedIn 재작성 필요 여부


#################################
# 라우터 — 요청 분류
#################################

class ContentChoice(BaseModel):
    """콘텐츠 타입 분류 결과"""
    content_type: Literal["linkedin", "instagram", "blog"] = Field(
        description="The type of content to generate", default="linkedin"
    )

# with_structured_output: LLM이 ContentChoice 형식으로만 응답하도록 강제
llm_with_content_choice = llm.with_structured_output(schema=ContentChoice)

def generate_content_router(state: WorkflowState) -> str:
    """사용자 요청을 분석해서 적절한 플랫폼으로 라우팅하는 conditional edge"""
    system_prompt = SystemMessage(content="""
    Classify the customer's request into one of:
    1. linkedin - LinkedIn post
    2. instagram - Instagram post
    3. blog - Blog post
    Default to 'linkedin' if not specified.
    """)
    response = llm_with_content_choice.invoke([system_prompt] + state.messages)
    content_type = response["content_type"] if isinstance(response, dict) else response.content_type
    print(f"\n🔀 라우터 결정: '{content_type}' 워크플로우로 분기")
    return content_type


#################################
# LinkedIn 플로우 (생성 → 검토 → 재작성 루프)
#################################

def generate_linkedin(state: WorkflowState):
    """LinkedIn 포스트 생성"""
    print("\n[LinkedIn] 포스트 생성 중...")
    system_prompt = SystemMessage(content="""
    You are a LinkedIn content creator specializing in AI topics.

    Requirements:
    - 150-300 words
    - 3-5 relevant hashtags
    - Conversational, professional tone
    - Start with a hook or thought-provoking question
    - End with a call-to-action
    - No title, get right into the post

    If given feedback, refine the draft based on it.
    """)
    response = llm.invoke([system_prompt] + state.messages)
    print(f"✅ LinkedIn 포스트 생성 완료 ({len(response.content)}자)")
    return {"content": response.content, "messages": [response], "rewrite": False}

class LinkedReview(BaseModel):
    """LinkedIn 포스트 검토 결과"""
    is_valid: bool = Field(..., description="Whether the post meets requirements")
    feedback: str | None = Field(None, description="Feedback if not valid")

llm_with_linkedin_format = llm.with_structured_output(schema=LinkedReview)

def review_linkedin(state: WorkflowState):
    """LinkedIn 포스트 품질 검토 — 기준 미달 시 재작성 요청"""
    print("\n[LinkedIn] 품질 검토 중...")
    system_prompt = SystemMessage(content=f"""
    Evaluate this LinkedIn post against these criteria:
    1. Includes 3-5 relevant hashtags
    2. Professional, conversational tone
    3. Starts with a hook
    4. Includes actionable takeaways
    5. Ends with a call-to-action

    Post: {state.content}

    Respond with is_valid and feedback if needed.
    """)
    response = llm_with_linkedin_format.invoke([system_prompt] + state.messages)
    is_valid = response["is_valid"] if isinstance(response, dict) else response.is_valid
    feedback = response.get("feedback") if isinstance(response, dict) else response.feedback

    if is_valid:
        print("✅ 품질 검토 통과!")
        return {"rewrite": False}
    else:
        print(f"⚠️  재작성 필요: {feedback}")
        return {"rewrite": True, "messages": feedback}

def linkedin_router(state: WorkflowState) -> str:
    """재작성 필요 여부에 따라 라우팅"""
    if state.rewrite:
        return "generate_linkedin"
    return END


#################################
# Instagram 플로우
#################################

def generate_instagram(state: WorkflowState):
    """Instagram 포스트 생성"""
    print("\n[Instagram] 포스트 생성 중...")
    system_prompt = SystemMessage(content="""
    You are an Instagram content creator specializing in AI topics.

    Requirements:
    - 150-250 words
    - At least 1 emoji
    - Strong hook (no title)
    - End with a question to encourage engagement
    """)
    response = llm.invoke([system_prompt] + state.messages)
    print(f"✅ Instagram 포스트 생성 완료 ({len(response.content)}자)")
    return {"content": response.content, "messages": [response]}


#################################
# Blog 플로우
#################################

def generate_blog(state: WorkflowState):
    """블로그 포스트 생성"""
    print("\n[Blog] 포스트 생성 중...")
    system_prompt = SystemMessage(content="""
    You are a blog writer specializing in AI topics.

    Requirements:
    - Introduction section
    - 3 body sections max
    - Conclusion with CTA
    - At least 3 emojis
    - SEO optimized
    """)
    response = llm.invoke([system_prompt] + state.messages)
    print(f"✅ 블로그 포스트 생성 완료 ({len(response.content)}자)")
    return {"content": response.content, "messages": [response]}


#################################
# 그래프 구성
#################################

builder = StateGraph(WorkflowState)

builder.add_node(generate_linkedin)
builder.add_node(review_linkedin)
builder.add_node(generate_instagram)
builder.add_node(generate_blog)

# START에서 라우터로 분기
builder.add_conditional_edges(
    START,
    generate_content_router,
    {
        "linkedin": "generate_linkedin",
        "instagram": "generate_instagram",
        "blog": "generate_blog",
    }
)

# LinkedIn: 생성 → 검토 → (재작성 or 종료) 루프
builder.add_edge("generate_linkedin", "review_linkedin")
builder.add_conditional_edges(
    "review_linkedin",
    linkedin_router,
    {"generate_linkedin": "generate_linkedin", END: END}
)

# Instagram, Blog: 생성 후 바로 종료
builder.add_edge("generate_instagram", END)
builder.add_edge("generate_blog", END)

graph = builder.compile()

# 실행 — 플랫폼을 명시하면 해당 워크플로우로 라우팅됨
query = "How MCPs just unlocked $100B in value for Google - for instagram"
print(f"\n입력: {query}")

response = graph.invoke(WorkflowState(messages=[query]))

print("\n" + "=" * 50)
print("  📄 생성된 콘텐츠")
print("=" * 50)
print(response["content"])
