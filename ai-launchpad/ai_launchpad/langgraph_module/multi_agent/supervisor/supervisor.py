"""
슈퍼바이저 에이전트 (Supervisor Agent) — 멀티 에이전트 조율자

사용자와 직접 대화하며 리서처와 카피라이터 서브에이전트에게 작업을 위임합니다.

## 전체 흐름
    사용자 요청
        → supervisor (계획 수립 + 작업 위임)
            → call_researcher (리서치 태스크)
                → researcher 서브그래프 (웹 검색 + 보고서)
            → call_researcher (추가 리서치, 필요 시 반복)
            → call_copywriter (콘텐츠 생성)
                → copywriter 서브그래프 (보고서 기반 작성)
        → supervisor (결과 요약 후 사용자에게 전달)

## 핵심 패턴
- Command 프리미티브: 도구 내에서 상태 업데이트 + 다음 노드 지정
- 서브그래프: 각 에이전트가 독립적인 그래프로 실행
- research_reports: supervisor ↔ researcher ↔ copywriter 간 공유 상태

## 실행 방법
    cd ai_launchpad/langgraph_module/multi_agent/supervisor
    uv run python main.py
    (GOOGLE_API_KEY, TAVILY_API_KEY 필요)
"""
import operator
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Annotated, Literal
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, add_messages, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime
from ai_launchpad.langgraph_module.multi_agent.supervisor.researcher import graph as research_agent
from ai_launchpad.langgraph_module.multi_agent.supervisor.copywriter import graph as copywriter_agent
from langgraph.types import Command, RunnableConfig

load_dotenv()

# 파일 위치 기준 절대 경로로 프롬프트 로드
_DIR = os.path.dirname(os.path.abspath(__file__))
supervisor_prompt = open(os.path.join(_DIR, "prompts/supervisor.md"), "r").read()


#################################
# State
#################################

class SupervisorState(BaseModel):
    """슈퍼바이저 에이전트 상태.
    research_reports는 researcher와 copywriter 서브에이전트와 공유됩니다.
    """
    messages: Annotated[list, add_messages] = []
    research_reports: Annotated[list, operator.add] = []  # 서브에이전트 간 공유
    task_description: str | None = None                    # 서브에이전트에게 전달할 태스크


#################################
# 핸드오프 도구
#################################

@tool
async def handoff_to_subagent(
    agent_name: Literal["researcher", "copywriter"],
    task_description: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Assign a task to a sub-agent.

    Args:
        agent_name: The agent to assign the task to ('researcher' or 'copywriter').
        task_description: Detailed description of the task to complete.
    """
    # Command 프리미티브: 상태 업데이트 + 다음 노드로 이동을 동시에 처리
    return Command(
        goto=f"call_{agent_name}",   # 다음으로 이동할 노드
        update={
            "task_description": task_description,
            "messages": [ToolMessage(
                name=f"handoff_to_{agent_name}",
                content=f"Task handed off to {agent_name}: {task_description[:100]}...",
                tool_call_id=tool_call_id,
            )],
        }
    )


#################################
# 서브에이전트 호출 노드
#################################

async def call_researcher(state: SupervisorState, config: RunnableConfig):
    """리서처 서브에이전트를 호출합니다.
    supervisor의 전체 대화 히스토리 대신 태스크 설명만 전달해서 컨텍스트를 깔끔하게 유지합니다.
    """
    print(f"\n  🔬 [Researcher] 리서치 시작: {state.task_description[:80]}...")
    research_response = await research_agent.ainvoke(
        input={"messages": [HumanMessage(content=state.task_description)]},
        config=config,
    )

    ai_message = AIMessage(
        name="researcher",
        content=research_response["messages"][-1].content
    )
    print(f"  ✅ [Researcher] 보고서 생성 완료")
    return {
        "research_reports": research_response["research_reports"],
        "messages": [ai_message],
    }


async def call_copywriter(state: SupervisorState, config: RunnableConfig):
    """카피라이터 서브에이전트를 호출합니다.
    태스크 설명과 함께 researcher가 생성한 모든 보고서를 전달합니다.
    """
    print(f"\n  ✍️  [Copywriter] 콘텐츠 작성 시작...")
    copywriter_response = await copywriter_agent.ainvoke(
        input={
            "messages": [HumanMessage(content=state.task_description)],
            "research_reports": state.research_reports,  # 리서치 보고서 공유
        },
        config=config,
    )

    ai_message = AIMessage(
        name="copywriter",
        content=copywriter_response["messages"][-1].content
    )
    print(f"  ✅ [Copywriter] 콘텐츠 생성 완료")
    return {"messages": [ai_message]}


#################################
# 슈퍼바이저 에이전트
#################################

# Gemma 4 31B 모델 사용 (agent_from_scratch와 동일)
llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)

tools = [handoff_to_subagent]
llm_with_tools = llm.bind_tools(tools)


async def supervisor(state: SupervisorState):
    """슈퍼바이저 에이전트 노드 — 계획 수립 및 서브에이전트 조율"""
    response = llm_with_tools.invoke([
        SystemMessage(content=supervisor_prompt.format(current_datetime=datetime.now()))
    ] + state.messages)
    return {"messages": [response]}


async def supervisor_router(state: SupervisorState) -> str:
    """도구 호출 여부에 따라 라우팅"""
    if state.messages[-1].tool_calls:
        return "tools"
    return END


#################################
# 그래프 구성
#################################

builder = StateGraph(SupervisorState)

builder.add_node(supervisor)
builder.add_node("tools", ToolNode(tools))
builder.add_node(call_researcher)
builder.add_node(call_copywriter)

builder.set_entry_point("supervisor")

builder.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {"tools": "tools", END: END}
)

# Command 프리미티브가 tools → call_researcher/call_copywriter 라우팅을 담당
# 서브에이전트 완료 후 항상 supervisor로 복귀
builder.add_edge("call_researcher", "supervisor")
builder.add_edge("call_copywriter", "supervisor")

# 부모 그래프에만 checkpointer 설정 (서브그래프는 상속)
graph = builder.compile(checkpointer=MemorySaver())
