"""
오케스트레이터-워커 (Orchestrator-Workers) — 동적 작업 분배

오케스트레이터가 복잡한 목표를 분석해서 필요한 서브태스크를 동적으로 결정하고
워커들에게 병렬로 할당하는 패턴입니다.

예제: 딥 리서치 워크플로우
    orchestrator (질문 분해) → researchers (병렬 웹 검색) → synthesizer (최종 보고서)

병렬화와의 차이:
- 병렬화: 미리 정해진 고정 작업들을 동시에 실행
- 오케스트레이터-워커: 오케스트레이터가 런타임에 작업 수와 내용을 결정

## 핵심 개념
1. 동적 작업 분해: 오케스트레이터가 3~7개의 서브태스크를 결정합니다.
2. Send API: LangGraph의 Send를 사용해 각 워커를 독립적으로 스폰합니다.
3. WorkerState: 각 워커가 독립적인 상태를 가집니다.
4. operator.add: 워커 결과를 자동으로 부모 상태에 누적합니다.

## 실행 방법
    uv run python workflows/6_orchestrator-workers.py
    (TAVILY_API_KEY 필요)
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, add_messages, END, START
from langgraph.types import Send
from langchain_tavily import TavilySearch, TavilyExtract
import operator

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)

print("=" * 50)
print("  📌 오케스트레이터-워커: 딥 리서치")
print("  질문 분해 → 병렬 웹 검색 → 최종 보고서")
print("=" * 50)


#################################
# 데이터 모델
#################################

class ResearchTask(BaseModel):
    """개별 워커에게 할당될 리서치 태스크"""
    topic: str
    search_query: str
    task: str

class ResearchTasks(BaseModel):
    """오케스트레이터가 생성하는 태스크 목록"""
    tasks: list[ResearchTask] = []

class CompletedTask(BaseModel):
    """워커가 완료한 태스크와 결과 보고서"""
    task: ResearchTask
    report: str


#################################
# State
#################################

class WorkflowState(BaseModel):
    """전체 워크플로우 상태"""
    messages: Annotated[list, add_messages] = []
    tasks: list[ResearchTask] = []                                    # 오케스트레이터가 생성한 태스크들
    completed_tasks: Annotated[list[CompletedTask], operator.add] = []  # 워커들의 결과 (자동 누적)
    final_report: str | None = None


#################################
# 오케스트레이터 — 태스크 분해
#################################

orchestrator_llm = llm.with_structured_output(schema=ResearchTasks)

def orchestrator(state: WorkflowState):
    """사용자 질문을 3~7개의 독립적인 리서치 태스크로 분해합니다."""
    print("\n[오케스트레이터] 질문 분해 중...")
    system_prompt = SystemMessage(content="""
    You are a research orchestrator. Decompose the user's query into 3-5 distinct, self-contained research tasks.

    Each task must be:
    - Independent (workers don't know about each other or the overall goal)
    - Specific and well-defined
    - Accompanied by a targeted search query

    Output as structured JSON.
    """)
    response = orchestrator_llm.invoke([system_prompt] + state.messages)
    print(f"✅ 태스크 {len(response.tasks)}개 생성:")
    for i, task in enumerate(response.tasks, 1):
        print(f"   {i}. {task.topic}")
    return {"tasks": response.tasks}

def researcher_router(state: WorkflowState):
    """각 태스크에 대해 독립적인 researcher 워커를 스폰합니다."""
    if state.tasks:
        # Send API: 각 태스크마다 researcher 노드를 별도로 실행
        # 워커 수는 오케스트레이터가 결정 — 미리 알 필요 없음
        return [Send("researcher", {"task": task}) for task in state.tasks]


#################################
# 워커 — 독립적인 리서치
#################################

class WorkerState(BaseModel):
    """개별 워커의 상태 — 메인 상태와 독립적"""
    task: ResearchTask
    completed_tasks: Annotated[list[CompletedTask], operator.add]

tavily_search = TavilySearch(max_results=2, topic="general")
tavily_extract = TavilyExtract()

def researcher(state: WorkerState):
    """할당된 태스크에 대해 웹 검색 및 내용 추출 후 보고서 작성"""
    print(f"\n[워커] '{state['task'].topic}' 리서치 중...")
    system_prompt = SystemMessage(content="""
    You are a specialized research agent. Synthesize the provided search results to answer your assigned task.

    Instructions:
    - Focus only on your task
    - Present key insights as bullet points
    - Include source URLs
    - Do not speculate — base answers on search results only
    """)

    # 웹 검색
    compressed_context = {"query": state["task"].search_query, "results": []}
    search_results = tavily_search.invoke(input={"query": state["task"].search_query})

    # 각 검색 결과의 본문 추출
    for result in search_results.get("results", []):
        try:
            extracted = tavily_extract.invoke(input={"urls": [result["url"]]})
            raw_content = extracted["results"][0]["raw_content"]
            compressed_context["results"].append({
                "title": result["title"],
                "url": result["url"],
                "content": raw_content
            })
        except:
            continue

    research_context = HumanMessage(
        content=f"Task: {state['task'].task}\n\n<SEARCH RESULTS>\n{str(compressed_context)}\n</SEARCH RESULTS>"
    )

    response = llm.invoke([system_prompt, research_context])
    print(f"✅ '{state['task'].topic}' 완료")

    # completed_tasks에 결과 추가 — operator.add로 자동 누적됨
    return {"completed_tasks": [CompletedTask(task=state["task"], report=response.content)]}


#################################
# 신시사이저 — 최종 보고서 합성
#################################

def synthesizer(state: WorkflowState):
    """모든 워커의 보고서를 하나의 종합 보고서로 합칩니다."""
    print(f"\n[신시사이저] {len(state.completed_tasks)}개 보고서 합성 중...")
    system_prompt = SystemMessage(content="""
    You are a senior research analyst. Combine the outputs of multiple research agents into a single comprehensive report.

    Instructions:
    - Integrate findings into logical sections
    - Resolve overlaps and contradictions
    - Include a sources section with all URLs
    - Format as well-structured markdown
    - Write like a McKinsey research report
    """)

    reports = "\n\n".join([
        f"=== {t.task.topic} ===\n{t.report}"
        for t in state.completed_tasks
    ])
    response = llm.invoke([system_prompt, HumanMessage(content=reports)])
    print("✅ 최종 보고서 생성 완료")
    return {"final_report": response.content}


#################################
# 그래프 구성
#################################

builder = StateGraph(WorkflowState)

builder.add_node(orchestrator)
builder.add_node(researcher)
builder.add_node(synthesizer)

builder.set_entry_point("orchestrator")
builder.add_conditional_edges("orchestrator", researcher_router, ["researcher"])
builder.add_edge("researcher", "synthesizer")
builder.add_edge("synthesizer", END)

graph = builder.compile()

# 실행
query = "What is the impact of AI on the job market?"
print(f"\n질문: {query}")

response = graph.invoke(WorkflowState(messages=[query]))

print("\n" + "=" * 50)
print("  📄 최종 리서치 보고서")
print("=" * 50)
print(f"\n완료된 태스크 수: {len(response['completed_tasks'])}")
print("\n" + response["final_report"])
