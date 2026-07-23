"""
증강 LLM (Augmented LLM) — 에이전트의 핵심 빌딩 블록

기본 LLM에 메모리와 도구를 추가하면 '증강 LLM'이 됩니다.
증강 LLM은 에이전트의 핵심 구성 요소이지만, 아직 '자율성(agency)'이 없어서
진정한 에이전트라고 할 수는 없습니다.

## 핵심 개념
1. 메모리 (Memory): 대화 히스토리를 누적해서 전달 → LLM이 문맥을 유지할 수 있음
2. 도구 (Tools): @tool 데코레이터로 Python 함수를 LLM이 사용할 수 있는 도구로 변환
3. LangGraph State: 그래프 전체에서 공유되는 상태 객체
4. MemorySaver: thread_id로 대화를 구분해서 영구적으로 상태를 저장

## 실행 방법
    uv run python building_blocks/2_augmented_llm.py
"""
from dotenv import load_dotenv
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import Annotated
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, add_messages, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver


def extract_text(content) -> str:
    """Gemma 4는 thinking + text 블록을 리스트로 반환함. 텍스트 파트만 추출."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [c["text"] for c in content if isinstance(c, dict) and c.get("type") == "text"]
        return "\n".join(parts)
    return str(content)

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0.1,
)

print("=" * 50)
print("  📌 증강 LLM: 메모리 + 도구 추가")
print("=" * 50)


#################################
# 1. 메모리 추가 — 대화 히스토리
#################################

print("\n[1단계] 메모리 없이 대화 (Stateless)")
print("-" * 40)

messages = []
user_input = "Hello! I'm Keeyong."
messages.append(HumanMessage(content=user_input))

response = llm.invoke(messages)
print(f"나: {user_input}")
print(f"LLM: {extract_text(response.content)}")
messages.append(response)  # AIMessage 객체 그대로 추가 (content가 리스트여도 안전)

user_input = "What's my name?"
messages.append(HumanMessage(content=user_input))
response = llm.invoke(messages)
print(f"\n나: {user_input}")
print(f"LLM: {extract_text(response.content)}")
print("✅ 이제 전체 대화 히스토리를 전달하므로 이름을 기억합니다!")


#################################
# 2. LangGraph State
#################################

print("\n[2단계] LangGraph State — 그래프의 공유 상태")
print("-" * 40)

# State: 그래프의 모든 노드가 공유하는 데이터 저장소
# add_messages: 메시지를 덮어쓰지 않고 누적하는 리듀서
class AgentState(BaseModel):
    """에이전트의 상태 — 대화 히스토리를 저장"""
    messages: Annotated[list, add_messages] = []

def agent_node(state: AgentState):
    """상태의 메시지를 LLM에 전달하고 응답을 반환하는 노드"""
    response = llm.invoke(state.messages)
    return {"messages": [response]}

builder = StateGraph(AgentState)
builder.add_node(agent_node)
builder.set_entry_point("agent_node")
graph = builder.compile()

# 그래프 호출 1: 자기소개
user_input = "Hello! I'm Keeyong."
response = graph.invoke(input=AgentState(messages=[HumanMessage(content=user_input)]))
print(f"나: {user_input}")
for msg in response["messages"]:
    if msg.content:
        print(f"LLM: {extract_text(msg.content)}")

# 그래프 호출 2: 이름 질문 — 각 graph.invoke()는 독립적이므로 아직 기억 못함
user_input = "What's my name?"
response = graph.invoke(input=AgentState(messages=[HumanMessage(content=user_input)]))
print(f"\n나: {user_input}")
for msg in response["messages"]:
    if msg.content:
        print(f"LLM: {extract_text(msg.content)}")
print("⚠️  각 graph.invoke()는 독립적 — MemorySaver 없이는 기억 못합니다")


#################################
# 3. MemorySaver — 영구 상태 저장
#################################

print("\n[3단계] MemorySaver + thread_id — 대화 세션 유지")
print("-" * 40)

# MemorySaver를 checkpointer로 사용하면 thread_id별로 상태가 저장됨
graph = builder.compile(checkpointer=MemorySaver())
config = RunnableConfig(configurable={"thread_id": "session-1"})

user_input = "Hello! I'm Keeyong."
response = graph.invoke(input=AgentState(messages=[HumanMessage(content=user_input)]), config=config)
print(f"나: {user_input}")
for msg in response["messages"]:
    if msg.content:
        print(f"LLM: {extract_text(msg.content)}")

user_input = "What's my name?"
response = graph.invoke(input=AgentState(messages=[HumanMessage(content=user_input)]), config=config)
print(f"\n나: {user_input}")
for msg in response["messages"]:
    if msg.content:
        print(f"LLM: {extract_text(msg.content)}")
print("✅ 같은 thread_id로 호출하면 이전 대화를 기억합니다!")


#################################
# 4. 도구 (Tools) 추가
#################################

print("\n[4단계] 도구 추가 — LLM이 함수를 호출할 수 있게")
print("-" * 40)

# LLM만으로는 실제 데이터에 접근할 수 없음
response = llm.invoke([HumanMessage(content="Can you pull the customer data for John Doe?")])
print(f"도구 없이: {extract_text(response.content)}")
print("⚠️  LLM이 실제 DB에 접근할 수 없어 데이터를 가져오지 못합니다\n")

# @tool 데코레이터: Python 함수를 LLM이 사용할 수 있는 도구로 변환
@tool
def get_customer_data(customer_name: str) -> str:
    """Get customer data from the database"""
    return f"Customer Data for {customer_name}\nEmail: example@gmail.com"

# bind_tools(): LLM에 도구 목록을 연결
llm_with_tools = llm.bind_tools([get_customer_data])

messages = []
user_input = "Can you pull the customer data for John Doe?"
messages.append(HumanMessage(content=user_input))
response = llm_with_tools.invoke(messages)

# tool_calls가 있으면 LLM이 직접 답변 대신 도구 호출을 요청한 것
print(f"도구 호출 요청: {response.tool_calls}")

# 도구 직접 실행
if response.tool_calls:
    tool_call = response.tool_calls[0]
    tool_response = get_customer_data.invoke(tool_call["args"]["customer_name"])
    print(f"도구 실행 결과: {tool_response}")

    messages.append(response)
    messages.append(tool_response)
    final_response = llm_with_tools.invoke(messages)
    print(f"최종 답변: {extract_text(final_response.content)}")


#################################
# 5. LangGraph에서 도구 추가
#################################

print("\n[5단계] LangGraph + ToolNode — 자동 도구 실행")
print("-" * 40)

tools = [get_customer_data]
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state.messages)
    return {"messages": [response]}

def agent_router(state: AgentState) -> str:
    """tool_calls가 있으면 tools 노드로, 없으면 종료"""
    if state.messages[-1].tool_calls:
        return "tools"
    return END

builder = StateGraph(AgentState)
builder.add_node(agent_node)
# ToolNode: 도구 호출 파싱 + 실행 + 결과 반환을 자동으로 처리
builder.add_node("tools", ToolNode(tools))
builder.set_entry_point("agent_node")
builder.add_conditional_edges("agent_node", agent_router, {"tools": "tools", END: END})
builder.add_edge("tools", "agent_node")  # 도구 실행 후 다시 에이전트로

graph = builder.compile()

response = graph.invoke(AgentState(messages=[HumanMessage(content="Can you pull the customer data for John Doe?")]))
print("전체 대화 흐름:")
for msg in response["messages"]:
    if msg.content:
        role = "LLM" if hasattr(msg, 'tool_calls') else "Tool"
        print(f"  {role}: {extract_text(msg.content)}")
