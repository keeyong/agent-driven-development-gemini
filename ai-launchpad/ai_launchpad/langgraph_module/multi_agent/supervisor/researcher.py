"""
리서처 서브에이전트 (Researcher Sub-agent)

Supervisor로부터 리서치 태스크를 받아 웹 검색 및 내용 추출 후 보고서를 생성합니다.
Supervisor 그래프의 서브그래프로 실행됩니다.

## 도구
- search_web: Tavily 웹 검색
- extract_content_from_webpage: 웹페이지 본문 추출
- generate_research_report: 리서치 보고서 생성 및 상태 저장

## 중요
- 서브그래프이므로 checkpointer를 직접 사용하지 않습니다.
  부모(supervisor) 그래프의 checkpointer를 상속합니다.
- research_reports 필드는 supervisor 상태와 필드명이 같아야 공유됩니다.
"""
import operator
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Annotated, List
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import StateGraph, add_messages, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool, InjectedToolCallId
from langchain_tavily import TavilySearch, TavilyExtract
from datetime import datetime
from langgraph.types import Command

load_dotenv()

# 파일 위치 기준 절대 경로로 프롬프트 로드 (실행 위치와 무관하게 동작)
_DIR = os.path.dirname(os.path.abspath(__file__))
researcher_prompt = open(os.path.join(_DIR, "prompts/researcher.md"), "r").read()


#################################
# 도구 정의
#################################

@tool
async def search_web(query: str, num_results: int = 3):
    """Search the web and get back results including title, url, and content preview.

    Args:
        query: The search query.
        num_results: The number of results to return, max is 3.
    """
    print(f"    🔍 [search_web] 검색어: '{query}' (최대 {min(num_results, 3)}개)")
    web_search = TavilySearch(max_results=min(num_results, 3), topic="general")
    search_results = web_search.invoke(input={"query": query})

    processed_results = {"query": query, "results": []}
    for result in search_results.get("results", []):
        processed_results["results"].append({
            "title": result["title"],
            "url": result["url"],
            "content_preview": result["content"]
        })

    print(f"    ✅ [search_web] {len(processed_results['results'])}개 결과 수신")
    return processed_results


@tool
async def extract_content_from_webpage(urls: List[str]):
    """Extract the full content from one or more webpages.

    Args:
        urls: List of URLs to extract content from.
    """
    print(f"    🌐 [extract_content] {len(urls)}개 URL 본문 추출 중...")
    for url in urls:
        print(f"       - {url}")

    web_extract = TavilyExtract()
    results = web_extract.invoke(input={"urls": urls})["results"]

    print(f"    ✅ [extract_content] 추출 완료 ({len(results)}개)")
    return results


class ResearchReport(BaseModel):
    """리서치 보고서 데이터 모델"""
    topic: str
    report: str


@tool
async def generate_research_report(
    topic: str,
    report: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Generate and save a research report on a specific topic.
    MUST be called at the end of every research task.

    Args:
        topic: The topic researched.
        report: The research report in markdown format with citations.
    """
    print(f"    📝 [generate_report] 보고서 생성 중: '{topic}'")
    research_report = ResearchReport(topic=topic, report=report)
    print(f"    ✅ [generate_report] 보고서 완성 ({len(report)}자)")

    # Command: research_reports 상태에 보고서 추가 (operator.add로 누적)
    # supervisor → copywriter로 이 보고서가 전달됨
    return Command(update={
        "research_reports": [research_report],
        "messages": [ToolMessage(
            name="generate_research_report",
            content=research_report.model_dump_json(),
            tool_call_id=tool_call_id,
        )],
    })


#################################
# State
#################################

class ResearcherState(BaseModel):
    """리서처 에이전트 상태.
    research_reports는 supervisor 상태와 필드명이 같아야 자동으로 공유됩니다.
    """
    messages: Annotated[list, add_messages] = []
    research_reports: Annotated[list, operator.add] = []  # supervisor와 공유


#################################
# 그래프 구성
#################################

tools = [search_web, extract_content_from_webpage, generate_research_report]

# Gemma 4 31B 모델 사용 (agent_from_scratch와 동일)
llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)
llm_with_tools = llm.bind_tools(tools)


async def researcher(state: ResearcherState):
    """리서처 에이전트 노드 — 웹 검색 후 리서치 보고서 생성"""
    response = llm_with_tools.invoke([
        SystemMessage(content=researcher_prompt.format(current_datetime=datetime.now()))
    ] + state.messages)
    return {"messages": [response]}


async def researcher_router(state: ResearcherState) -> str:
    """도구 호출 여부에 따라 라우팅.
    tool_calls 있으면 → tools 노드, 없으면 → 종료 (supervisor로 복귀)
    """
    if state.messages[-1].tool_calls:
        return "tools"
    return END


# 서브그래프 구성
# researcher → tools → researcher → ... → END
builder = StateGraph(ResearcherState)
builder.add_node(researcher)
builder.add_node("tools", ToolNode(tools))
builder.set_entry_point("researcher")
builder.add_edge("tools", "researcher")  # 도구 실행 후 항상 researcher로 복귀
builder.add_conditional_edges(
    "researcher",
    researcher_router,
    {"tools": "tools", END: END}
)

# 서브그래프: checkpointer 없이 컴파일 (부모 supervisor 그래프의 checkpointer를 상속)
graph = builder.compile()
