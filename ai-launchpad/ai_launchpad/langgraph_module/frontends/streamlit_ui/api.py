"""
LangGraph Server API 클라이언트

Streamlit UI가 LangGraph Server(localhost:2024)와 통신하기 위한 함수 모음입니다.
langgraph_sdk를 사용해 REST API를 래핑합니다.

## 주요 개념
- Assistant: LangGraph Server에 로드된 에이전트 (langgraph.json에 정의)
- Thread: 하나의 대화 세션 (사용자별로 여러 개 존재 가능)
- Run: Thread 내에서 에이전트를 실행하는 단위

## 전제 조건
LangGraph Server가 실행 중이어야 합니다:
    cd ai_launchpad/langgraph_module/langgraph_server
    langgraph dev
→ http://localhost:2024 에서 API 문서 확인 가능
"""
from langgraph_sdk import get_sync_client
from dotenv import load_dotenv
from typing import Any

load_dotenv()

# LangGraph Server 주소 (로컬 개발 환경)
# 프로덕션 배포 시 이 URL을 배포된 서버 주소로 변경
LANGGRAPH_API_URL = "http://localhost:2024"

# langgraph_sdk 클라이언트 초기화 — 모든 API 요청을 이 클라이언트로 처리
client = get_sync_client(url=LANGGRAPH_API_URL)


#################################
# Assistant API
#################################

def get_assistants():
    """LangGraph Server에 로드된 모든 에이전트(Assistant) 목록을 반환합니다.
    langgraph.json에 정의된 Researcher, Planner, LinkedInWriter 등이 여기 포함됩니다.
    """
    return client.assistants.search()


#################################
# Thread (대화 세션) API
#################################

def create_thread(user_id: str):
    """새 대화 스레드를 생성합니다.
    user_id를 메타데이터로 저장해 사용자별 대화 구분을 가능하게 합니다.
    """
    return client.threads.create(metadata={"user_id": user_id})


def search_threads(user_id: str):
    """특정 사용자의 모든 대화 스레드를 조회합니다."""
    return client.threads.search(metadata={"user_id": user_id})


def delete_thread(thread_id: str):
    """특정 스레드를 삭제합니다."""
    return client.threads.delete(thread_id)


def delete_all_threads(user_id: str):
    """특정 사용자의 모든 스레드를 삭제합니다. (개발/테스트용 정리 도구)"""
    threads = search_threads(user_id)
    for thread in threads:
        delete_thread(thread["thread_id"])


def get_thread_state(thread_id: str):
    """스레드의 현재 상태(메시지 히스토리 포함)를 반환합니다.
    Streamlit UI에서 이전 대화를 복원할 때 사용합니다.
    """
    return client.threads.get_state(thread_id)


#################################
# Run (에이전트 실행) API
#################################

def run_thread_stream(assistant_id: str, thread_id: str, input: dict[str, Any]):
    """에이전트를 실행하고 응답을 스트리밍으로 yield합니다.

    stream_mode="messages-tuple"로 메시지 청크를 실시간으로 받아
    Streamlit의 st.write_stream()에 전달합니다.

    Args:
        assistant_id: 실행할 에이전트의 ID
        thread_id: 대화 스레드 ID
        input: 에이전트에 전달할 입력 (예: {"messages": ["안녕하세요"]})

    Yields:
        str: 스트리밍 응답 텍스트 또는 도구 호출 정보
    """
    for chunk in client.runs.stream(
        thread_id=thread_id,
        assistant_id=assistant_id,
        input=input,
        stream_mode="messages-tuple",
    ):
        # "messages" 이벤트만 처리 (metadata, error 등은 무시)
        if chunk.event == "messages":
            if chunk.data[0]["type"] == "AIMessageChunk":
                if chunk.data[0]["tool_call_chunks"]:
                    # 도구 호출 시: 도구 이름과 인자를 스트리밍
                    tool_chunk = chunk.data[0]["tool_call_chunks"][0]
                    if tool_chunk["name"]:
                        yield tool_chunk["name"]
                    else:
                        yield tool_chunk["args"]
                else:
                    # 일반 텍스트 응답: 내용을 스트리밍
                    yield chunk.data[0]["content"]


#################################
# 개발 도구 (정리용)
#################################

async def main():
    """특정 사용자의 모든 스레드를 삭제합니다.
    개발/테스트 중 LangGraph Server 환경을 초기화할 때 사용합니다.

    실행:
        uv run python -m ai_launchpad.langgraph_module.frontends.streamlit_ui.api
    """
    user_id = "kenny"
    print(f"[cleanup] '{user_id}'의 모든 스레드 삭제 중...")
    delete_all_threads(user_id)
    print("[cleanup] 완료")


if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
