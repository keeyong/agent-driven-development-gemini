"""
평가자-최적화기 (Evaluator-Optimizer) — 반복적 품질 개선

결과물을 생성하고, 평가하고, 기준 미달 시 개선하는 루프를 반복하는 패턴입니다.

예제: Python 코드 생성기
    generate_code → evaluate_code → (기준 미달이면 다시 generate_code)
                                    (통과하면 END)

## 핵심 개념
1. 평가 기준: 하드코딩(컴파일 여부) 또는 LLM-as-a-judge(코드 품질) 방식 모두 가능합니다.
2. 피드백 루프: 평가자의 피드백이 생성자에게 전달되어 반복 개선됩니다.
3. 언제 사용: 평가 기준이 명확하고 반복 개선으로 품질이 향상되는 작업에 적합합니다.
4. 언제 사용하지 말아야 하는가: 평가 기준이 모호하거나 한 번의 생성으로 충분한 경우.

## 실행 방법
    uv run python workflows/7_evaluator-optimizer.py
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, add_messages, END, START
from langgraph.types import RunnableConfig

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)

print("=" * 50)
print("  📌 평가자-최적화기: 코드 생성 + 반복 개선")
print("  generate → evaluate → (개선 or 완료)")
print("=" * 50)


#################################
# State
#################################

class CodeReview(BaseModel):
    """코드 검토 결과"""
    is_valid: bool = Field(..., description="Whether the code meets all requirements")
    feedback: str | None = Field(None, description="Specific feedback if improvements needed")

class WorkflowState(BaseModel):
    """코드 생성 워크플로우 상태"""
    messages: Annotated[list, add_messages] = []
    code: str | None = None               # 생성된 코드
    code_review: CodeReview | None = None  # 검토 결과
    iteration: int = 0                    # 반복 횟수 추적


#################################
# 생성자 — 코드 생성/개선
#################################

def generate_code(state: WorkflowState):
    """요구사항 또는 피드백을 바탕으로 코드를 생성/개선합니다."""
    iteration = state.iteration + 1
    print(f"\n[생성 {iteration}회차] 코드 생성 중...")

    system_prompt = SystemMessage(content="""
    You are a code generator. Write clean, functional Python code.

    Instructions:
    - Solve the given problem correctly
    - Include error handling where appropriate
    - Use clear variable names and brief comments
    - Focus on correctness first, then readability

    Output only the code (no explanation).
    """)

    # 이전 코드와 피드백이 있으면 개선 모드
    if state.code and state.code_review and not state.code_review.is_valid:
        feedback_msg = HumanMessage(content=f"Previous code:\n{state.code}\n\nFeedback:\n{state.code_review.feedback}")
        response = llm.invoke([system_prompt] + state.messages + [feedback_msg])
        print(f"   ↻ 피드백 반영하여 개선 중...")
    else:
        response = llm.invoke([system_prompt] + state.messages)

    print(f"✅ 코드 생성 완료 ({len(response.content)}자)")
    return {"code": response.content, "iteration": iteration}


#################################
# 평가자 — 코드 품질 검토
#################################

code_review_llm = llm.with_structured_output(schema=CodeReview)

def evaluate_code(state: WorkflowState):
    """생성된 코드를 다음 기준으로 평가합니다:
    - 정확성: 요구사항을 올바르게 해결하는가?
    - 보안: 취약점이 있는가?
    - 성능: 비효율적인 부분이 있는가?
    - 코드 품질: 가독성과 유지보수성
    - 에러 처리: 엣지케이스 처리
    """
    print(f"\n[평가] 코드 검토 중...")
    system_prompt = f"""
    You are a code evaluator. Review this Python code:

    <CODE>
    {state.code}
    </CODE>

    Criteria:
    - Correctness: Does it solve the problem?
    - Security: Any vulnerabilities?
    - Performance: Any obvious inefficiencies?
    - Code quality: Readable and maintainable?
    - Error handling: Edge cases handled?

    If all criteria pass: is_valid=true
    If improvements needed: is_valid=false with specific actionable feedback as bullet points.
    """
    response = code_review_llm.invoke(system_prompt)
    is_valid = response["is_valid"] if isinstance(response, dict) else response.is_valid
    feedback = response.get("feedback") if isinstance(response, dict) else response.feedback

    if is_valid:
        print("✅ 검토 통과! 기준을 모두 충족합니다.")
    else:
        print(f"⚠️  개선 필요:\n{feedback}")

    return {"code_review": CodeReview(is_valid=is_valid, feedback=feedback)}

def evaluator_router(state: WorkflowState) -> str:
    """코드가 유효하면 종료, 아니면 다시 생성"""
    if state.code_review and state.code_review.is_valid:
        return END
    return "generate_code"


#################################
# 그래프 구성
#################################

builder = StateGraph(WorkflowState)

builder.add_node(generate_code)
builder.add_node(evaluate_code)

builder.set_entry_point("generate_code")
builder.add_edge("generate_code", "evaluate_code")
builder.add_conditional_edges(
    "evaluate_code",
    evaluator_router,
    {"generate_code": "generate_code", END: END}
)

graph = builder.compile()

# 실행
query = "Write a Python script that reads a CSV into a pandas DataFrame, plots a histogram of the first numeric column, and saves it to a PNG file."
print(f"\n요청: {query}")

response = graph.invoke(
    input=WorkflowState(messages=[query]),
    config=RunnableConfig(recursion_limit=15)  # 무한 루프 방지
)

print("\n" + "=" * 50)
print(f"  📄 최종 코드 (총 {response['iteration']}회 반복)")
print("=" * 50)
print(response["code"])
