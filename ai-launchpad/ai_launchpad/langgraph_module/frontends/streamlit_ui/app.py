"""
LangGraph 에이전트용 Streamlit 채팅 UI

LangGraph Server API를 통해 에이전트와 대화하는 웹 UI입니다.
- 사이드바: 에이전트 선택, 대화 목록 관리 (생성/삭제)
- 메인: 채팅 인터페이스 (스트리밍 응답, 도구 호출 결과 표시)

## 전제 조건
1. LangGraph Server가 실행 중이어야 합니다:
       cd ai_launchpad/langgraph_module/langgraph_server
       langgraph dev

2. Streamlit 실행:
       cd ai_launchpad/langgraph_module/frontends/streamlit_ui
       streamlit run app.py
"""
import streamlit as st
from ai_launchpad.langgraph_module.frontends.streamlit_ui.api import (
    get_assistants,
    create_thread,
    search_threads,
    get_thread_state,
    run_thread_stream,
    delete_thread,
)
import json


#################################
# 세션 상태 관리
#################################

def initialize_session_state(user_id: str):
    """앱 시작 시 세션 상태를 초기화합니다.

    st.session_state는 Streamlit의 서버 측 상태 저장소입니다.
    페이지가 새로 렌더링될 때도 값이 유지됩니다.

    Args:
        user_id: 사용자 식별자 — 스레드 태깅 및 검색에 사용
    """
    if "user_id" not in st.session_state:
        st.session_state.user_id = user_id

    if "assistants" not in st.session_state:
        # LangGraph Server에서 에이전트 목록 조회 → {이름: ID} 딕셔너리로 저장
        assistants_list = get_assistants()
        st.session_state.assistants = {
            assistant["name"]: assistant["assistant_id"]
            for assistant in assistants_list
        }

    if "active_assistant_id" not in st.session_state:
        # 기본값: 첫 번째 에이전트
        st.session_state.active_assistant_id = list(st.session_state.assistants.values())[0]

    if "thread_ids" not in st.session_state:
        # 해당 사용자의 기존 대화 스레드 목록 복원
        st.session_state.thread_ids = []
        threads = search_threads(st.session_state.user_id)
        for thread in threads:
            st.session_state.thread_ids.append(thread["thread_id"])

    if "selected_thread_id" not in st.session_state:
        # 기본값: 가장 최근 스레드 (없으면 None)
        if st.session_state.thread_ids:
            st.session_state.selected_thread_id = st.session_state.thread_ids[-1]
        else:
            st.session_state.selected_thread_id = None

    if "thread_state" not in st.session_state:
        st.session_state.thread_state = {}


def create_new_thread(user_id: str):
    """새 대화 스레드를 생성하고 선택 상태를 업데이트합니다."""
    thread = create_thread(user_id)
    st.session_state.thread_ids.append(thread["thread_id"])
    st.session_state.thread_state = get_thread_state(thread["thread_id"])
    st.session_state.selected_thread_id = thread["thread_id"]
    st.rerun()  # UI 새로 렌더링


def delete_thread_and_update_state(thread_id: str):
    """스레드를 삭제하고 세션 상태를 업데이트합니다."""
    delete_thread(thread_id)
    st.session_state.thread_ids.remove(thread_id)
    st.session_state.thread_state = {}
    st.rerun()


# 앱 시작 시 세션 초기화 (user_id는 실제 서비스에서 로그인 정보로 교체)
initialize_session_state(user_id="kenny")


#################################
# 사이드바 UI
#################################

with st.sidebar:
    st.write("User ID: " + st.session_state.user_id)

    # 에이전트 선택 드롭다운 (Researcher, Planner, LinkedInWriter 등)
    assistant = st.selectbox("Select Assistant", list(st.session_state.assistants.keys()))
    st.session_state.active_assistant_id = st.session_state.assistants[assistant]

    st.title("Conversations")

    if st.button("Create New Conversation"):
        create_new_thread(user_id=st.session_state.user_id)

    if st.session_state.thread_ids:
        def _on_select_thread():
            """다른 대화를 선택했을 때 해당 스레드의 메시지 히스토리를 로드"""
            st.session_state.thread_state = get_thread_state(st.session_state.selected_thread_id)

        # 선택된 스레드가 목록에 없으면 최신 스레드로 초기화
        if (
            "selected_thread_id" not in st.session_state
            or st.session_state.selected_thread_id not in st.session_state.thread_ids
        ):
            st.session_state.selected_thread_id = st.session_state.thread_ids[-1]

        # 대화 목록 라디오 버튼 (thread_id 앞 8자리만 표시)
        st.radio(
            "Select Conversation",
            options=st.session_state.thread_ids,
            format_func=lambda tid: tid[:8],
            key="selected_thread_id",
            on_change=_on_select_thread,
        )

    if st.button("Delete Conversation", type="primary"):
        if st.session_state.selected_thread_id:
            delete_thread_and_update_state(st.session_state.selected_thread_id)


#################################
# 메인 채팅 UI
#################################

st.title(f"Chatting with {assistant}")

# 선택된 스레드의 메시지 히스토리를 LangGraph Server에서 불러옴
if (
    st.session_state.selected_thread_id
    and st.session_state.selected_thread_id in st.session_state.thread_ids
):
    st.session_state.thread_state = get_thread_state(st.session_state.selected_thread_id)

# 스레드 상태의 메시지 목록을 순서대로 표시
if st.session_state.thread_state:
    for message in st.session_state.thread_state["values"].get("messages", []):
        if message["type"] == "tool":
            # 도구 실행 결과 → 접을 수 있는 expander로 표시
            with st.expander(f"🛠️ {message['name']} < RESULTS >"):
                try:
                    st.json(json.loads(message["content"]))
                except Exception:
                    st.write(message["content"])
        elif message["type"] == "ai" and message["tool_calls"]:
            # AI가 도구를 호출하는 메시지 → 도구 이름과 인자 표시
            with st.chat_message("ai"):
                st.markdown(f"🛠️ {message['tool_calls'][0]['name']} < CALL >")
                st.json(message["tool_calls"][0]["args"])
        else:
            # 일반 사용자/AI 메시지
            with st.chat_message(message["type"]):
                st.markdown(message["content"])

    # 사용자 입력창
    if prompt := st.chat_input("Send a message..."):
        # 사용자 메시지 즉시 표시 (다음 렌더링 전 미리 보여줌)
        with st.chat_message("user"):
            st.markdown(prompt)

        # 에이전트 응답 스트리밍 표시
        with st.chat_message("assistant"):
            stream = run_thread_stream(
                st.session_state.active_assistant_id,
                st.session_state.selected_thread_id,
                {"messages": [prompt]},
            )
            st.write_stream(stream)

        # 응답 완료 후 전체 UI 재렌더링 (thread_state에서 메시지 다시 로드)
        st.rerun()

else:
    st.write("Create a new conversation to start chatting...")


# 디버그 패널 — 사이드바 최하단에서 세션 상태 전체를 JSON으로 확인 가능
with st.expander("<DEBUG> Session State"):
    st.write(st.session_state)
