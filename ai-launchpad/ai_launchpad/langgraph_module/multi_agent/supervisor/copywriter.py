"""
카피라이터 서브에이전트 (Copywriter Sub-agent)

Supervisor로부터 콘텐츠 작성 태스크를 받아 LinkedIn 포스트 또는 블로그 포스트를 생성합니다.
researcher가 생성한 research_reports를 읽어 콘텐츠 작성에 활용합니다.

## 도구
- review_research_reports: 리서처가 생성한 보고서 조회
- generate_linkedin_post: LinkedIn 포스트 생성 및 파일 저장
- generate_blog_post: 블로그 포스트 생성 및 파일 저장

## 중요
- 서브그래프이므로 checkpointer를 직접 사용하지 않습니다.
- research_reports 필드는 supervisor가 주입해서 전달합니다.
- 생성된 파일은 ai_files/ 디렉토리에 저장됩니다.
"""
import operator
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Annotated
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, add_messages, END
from langgraph.prebuilt import ToolNode, InjectedState
from datetime import datetime

load_dotenv()

# 파일 위치 기준 절대 경로로 프롬프트/예시 로드 (실행 위치와 무관하게 동작)
_DIR = os.path.dirname(os.path.abspath(__file__))
copywriter_prompt = open(os.path.join(_DIR, "prompts/copywriter.md"), "r").read()
linkedin_example = open(os.path.join(_DIR, "example_content/linkedin.md"), "r").read()
blog_example = open(os.path.join(_DIR, "example_content/blog.md"), "r").read()

# 생성된 콘텐츠 저장 디렉토리 (없으면 자동 생성)
_AI_FILES_DIR = os.path.join(_DIR, "ai_files")
os.makedirs(_AI_FILES_DIR, exist_ok=True)


#################################
# State
#################################

class CopyWriterState(BaseModel):
    """카피라이터 에이전트 상태.
    research_reports는 supervisor가 전달해주는 공유 필드입니다.
    """
    messages: Annotated[list, add_messages] = []
    research_reports: Annotated[list, operator.add] = []  # supervisor에서 주입


#################################
# 도구 정의
#################################

@tool
async def review_research_reports(
    state: Annotated[CopyWriterState, InjectedState],
):
    """Review all available research reports to inform content writing.
    Always call this first before writing any content.
    """
    # InjectedState: 그래프 상태를 도구 인자로 자동 주입 (사용자가 직접 전달하지 않음)
    if not state.research_reports:
        print("    ⚠️  [review_reports] 사용 가능한 리서치 보고서 없음")
        return "No research reports available."

    print(f"    📖 [review_reports] 보고서 {len(state.research_reports)}개 조회")
    for i, report in enumerate(state.research_reports, 1):
        print(f"       {i}. {report.topic}")
    return [report.model_dump_json() for report in state.research_reports]


@tool
async def generate_linkedin_post(title: str, content: str):
    """Generate and save a LinkedIn post.

    Args:
        title: The title/filename for the post.
        content: The post content in markdown format.
    """
    filename = os.path.join(_AI_FILES_DIR, f"{title}.md")
    with open(filename, "w") as f:
        f.write(content)
    print(f"    💼 [linkedin_post] 저장 완료: {filename}")
    return f"LinkedIn post saved to {filename}"


@tool
async def generate_blog_post(title: str, content: str):
    """Generate and save a blog post.

    Args:
        title: The title/filename for the post.
        content: The post content in markdown format.
    """
    filename = os.path.join(_AI_FILES_DIR, f"{title}.md")
    with open(filename, "w") as f:
        f.write(content)
    print(f"    📝 [blog_post] 저장 완료: {filename}")
    return f"Blog post saved to {filename}"


#################################
# 그래프 구성
#################################

tools = [review_research_reports, generate_linkedin_post, generate_blog_post]

# Gemma 4 31B 모델 사용 (agent_from_scratch와 동일)
llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)
llm_with_tools = llm.bind_tools(tools)


async def copywriter(state: CopyWriterState):
    """카피라이터 에이전트 노드 — 리서치 보고서 기반 콘텐츠 생성"""
    system_prompt = SystemMessage(content=copywriter_prompt.format(
        current_datetime=datetime.now(),
        linkedin_example=linkedin_example,
        blog_example=blog_example,
    ))
    response = llm_with_tools.invoke([system_prompt] + state.messages)
    return {"messages": [response]}


async def copywriter_router(state: CopyWriterState) -> str:
    """도구 호출 여부에 따라 라우팅.
    tool_calls 있으면 → tools 노드, 없으면 → 종료 (supervisor로 복귀)
    """
    if state.messages[-1].tool_calls:
        return "tools"
    return END


# 서브그래프 구성
# copywriter → tools → copywriter → ... → END
builder = StateGraph(CopyWriterState)
builder.add_node(copywriter)
builder.add_node("tools", ToolNode(tools))
builder.set_entry_point("copywriter")
builder.add_conditional_edges(
    "copywriter",
    copywriter_router,
    {"tools": "tools", END: END}
)
builder.add_edge("tools", "copywriter")  # 도구 실행 후 항상 copywriter로 복귀

# 서브그래프: checkpointer 없이 컴파일 (부모 supervisor 그래프의 checkpointer를 상속)
graph = builder.compile()
