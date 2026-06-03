"""
메모리 관리 MCP 서버 (STDIO 방식)

이 파일은 FastMCP를 사용해 장기 기억을 관리하는 MCP 서버를 정의합니다.
main.py가 실행될 때 자식 프로세스로 자동 실행되며, STDIO(표준 입출력)로 통신합니다.
별도 터미널에서 미리 실행할 필요 없습니다.

제공하는 MCP 도구:
- manage_memories: 기억 생성/수정/삭제
- get_memories: 저장된 모든 기억 조회

운영 환경에서는 dict 대신 Postgres, Redis 등 영구 저장소를 사용해야 합니다.
"""
from fastmcp import FastMCP
from typing import Literal, Dict

# MCP 서버 생성. name은 클라이언트에서 도구를 구분할 때 prefix로 사용됨
# 예: manage_memories → memory_manage_memories
mcp = FastMCP(name="memory")

# 기억을 저장할 딕셔너리 (프로세스 종료 시 사라짐)
memories = {}


@mcp.tool()
def manage_memories(
    action: Literal["create", "update", "delete"],
    id: int,
    content: str | None = None
) -> Dict[int, str]:
    """Manage memories.

    Args:
        action (str): The memory action to perform. Can be one of "create", "update", or "delete".
        id (int): The id of the memory. Must be unique.
        content (str): The content of the memory. Only required when action is "create" or "update".

    Returns:
        The updated memories.
    """
    global memories
    if action == "create":
        if id in memories:
            raise ValueError(f"Memory with id {id} already exists.")
        if content is None:
            raise ValueError(f"Content cannot be None when creating memory with id {id}.")
        memories[id] = content

    elif action == "update":
        if id not in memories:
            raise ValueError(f"Memory with id {id} does not exist.")
        if content is None:
            raise ValueError(f"Content cannot be None when updating memory with id {id}.")
        memories[id] = content

    elif action == "delete":
        if id not in memories:
            raise ValueError(f"Memory with id {id} does not exist.")
        del memories[id]

    return memories


@mcp.tool()
def get_memories() -> Dict[int, str]:
    """Get all memories.

    Returns:
        The memories.
    """
    return memories


if __name__ == "__main__":
    # transport를 명시하지 않으면 기본값 STDIO로 실행됨
    # STDIO: main.py가 이 프로세스를 자식으로 실행하고 stdin/stdout으로 통신
    mcp.run()
