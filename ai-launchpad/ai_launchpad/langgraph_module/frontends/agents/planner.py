"""
플래너 에이전트 (Planner Agent) — LangGraph Server용

사용자의 태스크를 관리하는 개인 비서 에이전트입니다.
LangGraph Server(langgraph dev)에 로드되어 Streamlit UI 또는 REST API로 호출됩니다.

## 도구
- generate_task_list: 태스크 목록 생성 또는 전체 교체
- view_task_list: 현재 태스크 목록 조회

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
from pydantic import BaseModel, Field
from typing import Annotated, Literal, List  # noqa: F401
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, add_messages, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from datetime import datetime

load_dotenv()

# Gemma 4 31B 모델 사용 (Google AI)
llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)


#################################
# State & 데이터 모델
#################################

# 인메모리 태스크 저장소 (프로덕션에서는 Postgres, Redis 등으로 교체)
store = {}


class Task(BaseModel):
    """태스크 데이터 모델 — Pydantic으로 타입 검증"""
    task: str = Field(..., description="The task to be completed")
    status: Literal["todo", "in_progress", "done"] = Field(..., description="The status of the task")
    priority: int = Field(..., description="The priority of the task, 1 is the highest priority, 5 is the lowest")
    due_date: str | None = Field(None, description="The due date of the task, in the format of YYYY-MM-DD")


class TaskList(BaseModel):
    """태스크 목록 데이터 모델"""
    tasks: List[Task] = Field(..., description="The list of tasks to be completed")


class AgentState(BaseModel):
    """플래너 에이전트 상태 — 대화 히스토리를 누적 저장"""
    messages: Annotated[list, add_messages] = []


#################################
# 도구 정의
#################################

@tool
def generate_task_list(task_list: TaskList) -> str:
    """Generate a new task list or update the existing task list by replacing it.

    Args:
        task_list: The task list to generate or update.
    """
    print(f"  📋 [generate_task_list] {len(task_list.tasks)}개 태스크 저장")
    for t in task_list.tasks:
        print(f"     - [{t.priority}순위] {t.task} ({t.status})")
    store["tasks"] = task_list
    return store["tasks"].model_dump_json()


@tool
def view_task_list() -> str:
    """View the current task list."""
    if "tasks" not in store:
        print("  ⚠️  [view_task_list] 저장된 태스크 없음")
        return "No task list found."
    tasks = store["tasks"]
    print(f"  📖 [view_task_list] 태스크 {len(tasks.tasks)}개 조회")
    return tasks.model_dump_json()


#################################
# 그래프 구성
#################################

tools = [generate_task_list, view_task_list]
llm_with_tools = llm.bind_tools(tools)


def agent(state: AgentState):
    """플래너 에이전트 노드 — 태스크 생성 및 관리"""
    system_prompt = SystemMessage(content=f"""You are a personal assistant. Your job is to help the user manage their tasks. You have a couple of tools at your disposal to help you manage tasks.

    <Tools>
    generate_task_list: Use this tool to both create new task lists and/or make updates to the existing task list by replacing it.
    view_task_list: Use this tool to view the current task list.
    </Tools>

    <Tasks>
    Tasks include a task description, status, priority, and due date.
    </Tasks>

    Today's date is {datetime.now().date()}.
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
