"""
리서처 에이전트 (Researcher Agent) — LangGraph Server용

웹 검색을 통해 사용자의 질문에 답하는 리서치 에이전트입니다.
LangGraph Server(langgraph dev)에 로드되어 Streamlit UI 또는 REST API로 호출됩니다.

## 도구
- search_web: Tavily 웹 검색 (제목, URL, 요약 반환)
- extract_content_from_webpage: 특정 URL의 웹페이지 본문 전체 추출

## 실행 방법
이 파일은 단독 실행이 아닌 LangGraph Server에 로드됩니다.
  1. langgraph_server/ 디렉토리에서 실행:
       langgraph dev
  2. Streamlit UI 실행:
       cd frontends/streamlit_ui
       streamlit run app.py
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Annotated
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, add_messages, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_tavily import TavilySearch, TavilyExtract
from datetime import datetime

load_dotenv()

# Gemma 4 31B 모델 사용 (Google AI)
llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)


#################################
# State
#################################

class AgentState(BaseModel):
    """리서처 에이전트 상태 — 대화 히스토리를 누적 저장"""
    messages: Annotated[list, add_messages] = []


#################################
# 도구 정의
#################################

@tool
def search_web(query: str, num_results: int = 3):
    """Search the web and return results with title, url, and summary.

    Args:
        query: The search query.
        num_results: The number of results to return, max is 3.
    """
    print(f"  🔍 [search_web] 검색어: '{query}'")
    tavily_search = TavilySearch(max_results=min(num_results, 3), topic="general")
    search_results = tavily_search.invoke(input={"query": query})

    processed_results = {"query": query, "results": []}
    for result in search_results["results"]:
        processed_results["results"].append({
            "title": result["title"],
            "url": result["url"],
            "summary": result["content"]
        })

    print(f"  ✅ [search_web] {len(processed_results['results'])}개 결과 수신")
    return processed_results


@tool
def extract_content_from_webpage(url: str):
    """Extract the full content from a webpage given a URL.

    Args:
        url: The URL of the webpage to extract content from.
    """
    # TavilyExtract는 함수 내부에서 초기화 (모듈 로드 시 API 키 불필요)
    print(f"  🌐 [extract_content] URL 추출 중: {url}")
    result_contents = TavilyExtract().invoke(input={"urls": [url]})
    raw_content = result_contents["results"][0]["raw_content"]
    print(f"  ✅ [extract_content] 추출 완료 ({len(raw_content)}자)")
    return raw_content


#################################
# 그래프 구성
#################################

tools = [search_web, extract_content_from_webpage]
llm_with_tools = llm.bind_tools(tools)


def agent(state: AgentState):
    """리서처 에이전트 노드 — 웹 검색으로 질문에 답변"""
    system_prompt = SystemMessage(content=f"""You are a research assistant. Your job is to help the user answer questions by performing research. You have a couple of tools at your disposal to help you perform research.

    <Tools>
    search_web: Use this tool to search the web. Returned results include the page title, url, and a short summary of each webpage.
    extract_content_from_webpage: Use this tool to extract the complete contents from a webpage given the url.
    </Tools>

    The current date and time is {datetime.now()}.
    """)
    response = llm_with_tools.invoke([system_prompt] + state.messages)
    return {"messages": [response]}


def agent_router(state: AgentState) -> str:
    """도구 호출 여부에 따라 라우팅
    tool_calls 있으면 → tools, 없으면 → END
    """
    if state.messages[-1].tool_calls:
        return "tools"
    return END


# agent → tools → agent → ... → END
builder = StateGraph(AgentState)
builder.add_node(agent)
builder.add_node("tools", ToolNode(tools))
builder.set_entry_point("agent")
builder.add_edge("tools", "agent")  # 도구 실행 후 항상 agent로 복귀
builder.add_conditional_edges(
    "agent",
    agent_router,
    {"tools": "tools", END: END}
)

# LangGraph Server가 이 graph 객체를 로드해서 API로 노출
graph = builder.compile()
