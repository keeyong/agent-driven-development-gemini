"""
완전한 에이전트 (Full Agent) — LinkedIn 콘텐츠 크리에이터

앞서 배운 모든 개념을 합쳐서 실제로 동작하는 에이전트를 구현합니다.
에이전트는 도구를 자율적으로 선택하고, 스스로 계획을 세우고, 반복해서 작업을 수행합니다.

에이전트의 4가지 핵심 능력:
1. Agency (자율성): 다음 행동을 스스로 결정
2. Acting (행동): 도구로 환경에 작용
3. Perceiving (인식): 도구 결과를 보고 상황 파악
4. Self-refining (자기 개선): 실수에서 배우고 개선

## 도구 목록
- generate_task_list: 작업 계획 생성/업데이트
- view_task_list: 현재 작업 목록 확인
- search_web: Tavily 웹 검색
- extract_content_from_webpage: 웹페이지 본문 추출
- view_golden_posts: 우수 포스트 예시 조회

## 언제 에이전트를 쓰는가?
- 작업 단계의 수와 순서를 미리 알 수 없을 때
- 반면, 단계가 명확하다면 워크플로우(3~7번)가 더 낫습니다

## 실행 방법
    uv run python agents/8_agent.py
    (GOOGLE_API_KEY, TAVILY_API_KEY 필요)
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Annotated, Literal, List
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, AIMessageChunk
from langgraph.graph import StateGraph, add_messages, END
from langgraph.types import RunnableConfig
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langchain_tavily import TavilySearch, TavilyExtract
from datetime import datetime

load_dotenv()

print("=" * 50)
print("  📌 완전한 에이전트: LinkedIn 콘텐츠 크리에이터")
print("  자율적 계획 수립 → 도구 사용 → 포스트 생성")
print("=" * 50)

# gemma-4-31b-it: 도구 호출과 긴 컨텍스트를 잘 처리하는 Gemini 모델
llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)


#################################
# State
#################################

# 작업 목록 관리를 위한 데이터 모델
store = {}  # 인메모리 저장소 (운영 환경에서는 DB 사용)

class Task(BaseModel):
    """개별 태스크"""
    task: str = Field(..., description="The task to be completed")
    status: Literal["todo", "in_progress", "done"] = Field(..., description="Task status")

class TaskList(BaseModel):
    """태스크 목록"""
    tasks: List[Task] = Field(..., description="The list of tasks")

class AgentState(BaseModel):
    """에이전트 상태"""
    messages: Annotated[list, add_messages] = []
    post: str | None = None  # 최종 생성된 포스트


#################################
# 도구 정의
#################################

@tool
def generate_task_list(task_list: TaskList):
    """Generate a new task list or update the existing task list by replacing it."""
    store["tasks"] = task_list
    return store["tasks"].model_dump_json()

@tool
def view_task_list():
    """View the current task list."""
    if "tasks" not in store:
        return "No task list found."
    return store["tasks"].model_dump_json()

@tool
def search_web(query: str, num_results: int = 3):
    """Search the web and get back search results including title, url, and summary.

    Args:
        query: The search query.
        num_results: The number of results to return, max is 3.
    """
    tavily_search = TavilySearch(max_results=max(num_results, 3), topic="general")
    search_results = tavily_search.invoke(input={"query": query})

    processed_results = {"query": query, "results": []}
    for result in search_results.get("results", []):
        processed_results["results"].append({
            "title": result["title"],
            "url": result["url"],
            "summary": result["content"]
        })
    return processed_results

tavily_extract = TavilyExtract()

@tool
def extract_content_from_webpage(url: str):
    """Extract the full content from a webpage.

    Args:
        url: The URL of the webpage to extract content from.
    """
    result_contents = tavily_extract.invoke(input={"urls": [url]})
    return result_contents["results"][0]["raw_content"]

@tool
def view_golden_posts():
    """View examples of gold standard LinkedIn posts to use as writing reference."""
    return """
    <Examples>
        <Example_1>
        I hit 250,000 followers in 365 days.
        Not by doing more.
        By unlearning everything I was told about LinkedIn.

        Here's what actually moved the needle: 👇

        1. I stopped chasing vanity metrics
        146,000 likes? Didn't change my life.
        One DM: "You saved my career." That did.

        → Impressions = ego
        → Impact = legacy

        2. I stopped writing to impress
        I wrote what I needed to hear - back when I was 32, burnt out, and breaking down.
        250K didn't follow polish. They followed truth.

        3. I stopped copying "top creators"
        When I owned my voice, others saw themselves in it.

        The post you're scared to share is the one someone else needs.

        If this resonated, repost it.
        </Example_1>

        <Example_2>
        Talk is cheap. Your actions say everything.

        Not all feedback is created equal.

        It must come from people with the right attitude.
        Who have done what you're trying to do.

        🚫 Insecure individuals tear your ideas apart.
        ✅ Secure people support your ideas.

        🚫 Unsuccessful folks want you to fail.
        ✅ Successful people root for others.

        Who's in your circle that truly lifts you up?
        Tag them in the comments.

        ♻️ Repost to help someone upgrade their environment.
        </Example_2>
    </Examples>
    """


#################################
# 그래프 구성
#################################

tools = [generate_task_list, view_task_list, search_web, extract_content_from_webpage, view_golden_posts]
llm_with_tools = llm.bind_tools(tools)

def agent(state: AgentState):
    """에이전트 노드 — 다음 행동을 결정하고 실행"""
    system_prompt = SystemMessage(content=f"""You are a LinkedIn content creator specializing in AI topics.

    <Post_Requirements>
    - 100-300 words
    - Conversational, professional tone
    - Strong hook (surprising statement, statistic, or question)
    - Practical insights or actionable takeaways
    - Call-to-action at the end
    - At least 1 emoji
    - No title — get right into the post
    - Short paragraphs
    </Post_Requirements>

    <Guidelines>
    - Always create a plan first using generate_task_list
    - Check task status with view_task_list before each new task
    - Search the web for latest information — don't rely on existing knowledge
    - Before writing the final post, always use view_golden_posts for reference
    - Verify all tasks are complete before providing the final post
    </Guidelines>

    <Tools>
    generate_task_list: Create or update the task list
    view_task_list: Check current tasks and their status
    search_web: Search for latest information
    extract_content_from_webpage: Get full content from a URL
    view_golden_posts: View gold standard post examples before writing
    </Tools>

    Today's date: {datetime.now().strftime('%Y-%m-%d')}
    """)
    response = llm_with_tools.invoke([system_prompt] + state.messages)
    return {"messages": [response]}

def agent_router(state: AgentState) -> str:
    """도구 호출이 있으면 tools로, 없으면 종료"""
    if state.messages[-1].tool_calls:
        return "tools"
    return END

builder = StateGraph(AgentState)
builder.add_node(agent)
builder.add_node("tools", ToolNode(tools))
builder.set_entry_point("agent")
builder.add_edge("tools", "agent")
builder.add_conditional_edges("agent", agent_router, {"tools": "tools", END: END})

# MemorySaver: thread_id로 대화 세션 유지 (멀티턴 대화 가능)
graph = builder.compile(checkpointer=MemorySaver())


#################################
# 스트리밍 출력
#################################

async def stream_graph_responses(input: AgentState, graph: StateGraph, **kwargs):
    """에이전트 응답을 실시간으로 스트리밍합니다."""
    async for message_chunk, metadata in graph.astream(
        input=input,
        stream_mode="messages",
        **kwargs
    ):
        if isinstance(message_chunk, AIMessageChunk):
            if message_chunk.response_metadata:
                if message_chunk.response_metadata.get("finish_reason") == "tool_calls":
                    yield "\n\n"

            if message_chunk.tool_call_chunks:
                tool_chunk = message_chunk.tool_call_chunks[0]
                tool_name = tool_chunk.get("name", "")
                args = tool_chunk.get("args", "")
                if tool_name:
                    yield f"\n\n 🛠️  Tool: {tool_name}\n\n"
                if args:
                    yield args
            else:
                # Gemma 4는 content를 [{'type': 'thinking', ...}, {'type': 'text', ...}] 리스트로 반환
                # thinking 청크를 걸러내고 text 타입만 출력
                content = message_chunk.content
                if isinstance(content, str):
                    yield content
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            yield block.get("text", "")


async def main():
    print("\n예시 요청:")
    print("  - Create a post about how AI agents are changing the way we work")
    print("  - Create a post about why most AI projects fail")
    print("  - 'exit' 또는 'quit'으로 종료\n")

    config = RunnableConfig(configurable={
        "thread_id": "linkedin-agent-1",
        "recursion_limit": 30,
    })

    while True:
        user_input = input("\n\nUser: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\n\nExit command received. Exiting...\n\n")
            break

        print(f"\n\n ----- 🥷 Human ----- \n\n{user_input}\n")

        graph_input = AgentState(messages=[HumanMessage(content=user_input)])

        print(f" ---- 🤖 Agent ---- \n")
        async for response in stream_graph_responses(graph_input, graph, config=config):
            print(response, end="", flush=True)
        print("\n")  # 에이전트 응답 끝에 개행 추가


if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
