"""
FastMCP 클라이언트 데모

MCP 클라이언트가 서버에 연결해서 도구/리소스/프롬프트를 사용하는 방법을 보여줍니다.

실행 전 준비:
    1. retrieval MCP 서버를 별도 터미널에서 먼저 실행:
       uv run python tools/retrieval_mcp.py

    2. 이 파일 실행:
       uv run python 1_mcp_client_demo.py

MCP가 제공하는 세 가지 기능:
    - Tools     : 함수 호출 (부작용 있음, 검색/저장 등)
    - Resources : 읽기 전용 데이터 조회 (부작용 없음)
    - Prompts   : 프롬프트 템플릿 생성
"""
import json
import asyncio
from fastmcp import Client

# mcp_config.json에서 서버 연결 정보 로드
# memory 서버: STDIO (자동 실행), retrieval 서버: HTTP (미리 실행 필요)
with open("mcp_config.json", "r") as f:
    mcp_config = json.load(f)

mcp_client = Client(mcp_config)


async def main():
    # context manager: 블록 진입 시 MCP 서버들에 연결, 블록 종료 시 자동 해제
    async with mcp_client:

        # 연결된 모든 MCP 서버의 도구 목록 조회
        print("=" * 50)
        print("[도구 목록] 연결된 MCP 서버들의 사용 가능한 도구:")
        tools = await mcp_client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # 연결된 모든 MCP 서버의 리소스 목록 조회
        print("\n[리소스 목록] 읽기 전용 데이터 소스:")
        resources = await mcp_client.list_resources()
        for resource in resources:
            print(f"  - {resource.name}: {resource.uri}")

        # 연결된 모든 MCP 서버의 프롬프트 목록 조회
        print("\n[프롬프트 목록] 사용 가능한 프롬프트 템플릿:")
        prompts = await mcp_client.list_prompts()
        for prompt in prompts:
            print(f"  - {prompt.name}")

        # 리소스 조회: retrieval 서버의 마지막 업데이트 날짜
        print("\n[리소스 조회] status://retrieval/last_updated")
        resource_result = await mcp_client.read_resource("status://retrieval/last_updated")
        print(f"  결과: {resource_result}")

        # 도구 호출: memory 서버에 새 기억 생성
        print("\n[도구 호출] memory_manage_memories - 기억 생성")
        tool_result = await mcp_client.call_tool(
            "memory_manage_memories",
            {"action": "create", "id": 1, "content": "The user's name is Kenny."}
        )
        print(f"  결과: {tool_result}")

        # 도구 호출: memory 서버에서 모든 기억 조회
        print("\n[도구 호출] memory_get_memories - 기억 조회")
        tool_result = await mcp_client.call_tool("memory_get_memories", {})
        print(f"  결과: {tool_result}")

        # 프롬프트 호출: retrieval 서버의 고객 분석 프롬프트 생성
        print("\n[프롬프트 호출] retrieval_analyze_customer - 고객 분석 프롬프트 생성")
        prompt_result = await mcp_client.get_prompt("retrieval_analyze_customer", {"user_id": 1})
        print(f"  프롬프트 객체: {prompt_result}")

        # 실제 프롬프트 텍스트만 추출
        print("\n[프롬프트 텍스트]")
        print(prompt_result.messages[0].content.text)


def is_interactive():
    """Jupyter/IPython 같은 인터랙티브 환경인지 확인."""
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except ImportError:
        return False


if __name__ == "__main__":
    if is_interactive():
        # Jupyter에서는 이미 이벤트 루프가 실행 중이므로 nest_asyncio 필요
        import nest_asyncio
        nest_asyncio.apply()

    asyncio.run(main())
