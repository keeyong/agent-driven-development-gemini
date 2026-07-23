"""
Long-term memory allows agents to remember important context across different conversations and sessions.

## Memory Management
- In this simplified example, we will use a simple in-memory store (dictionary) to manage memories.
- In production, you would use a database like Postgres, MongoDB, or Redis for persistence.
- We're also giving the agent control over managing its own memories. This is a design choice. Sometimes it's better to manage memories externally to improve reliability, or use a combination of both.

## 이 파일의 전체 흐름

LLM은 기본적으로 대화가 끝나면 모든 것을 잊습니다 (stateless).
장기 기억(Long-term Memory)은 이 문제를 해결하기 위해, 중요한 정보를 외부 저장소에 저장하고
새 대화에서도 불러올 수 있게 하는 메커니즘입니다.

    [Part 1] 메모리 관리 함수 정의 및 테스트
             - manage_memories(): 기억 생성/수정/삭제
             - get_memories(): 저장된 모든 기억 조회

    [Part 2] 첫 번째 대화 - 새 정보 기억
             - 사용자가 이름/관계 정보를 알려줌
             - 모델이 manage_memories 도구 호출을 요청함
             - (실제 tool calling 루프는 2_tool_calling.py 참고)

    [Part 3] 두 번째 대화 - 기억 불러오기
             - 새 대화가 시작되어도 메모리는 유지됨
             - 모델이 get_memories를 먼저 호출해서 과거 정보를 확인한 후 답변

핵심 포인트:
- 메모리는 딕셔너리(dict)에 저장되므로 프로그램이 종료되면 사라짐 (in-memory).
- 실제 서비스에서는 DB(Postgres, Redis 등)에 저장해야 영구 보관 가능.
- 에이전트가 스스로 기억을 관리하는 방식 — 언제 저장/삭제할지를 LLM이 판단함.
"""
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal
import os

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-3.1-flash-lite"


##########################################
# Part 1. 메모리 관리 함수 정의 및 테스트
##########################################

# 메모리를 저장할 딕셔너리 (실제 서비스에서는 DB로 대체)
memories = {}


class Memory(BaseModel):
    id: int = Field(..., description="The id of the memory")
    content: str = Field(..., description="The content of the memory")


def manage_memories(
    action: Literal["create", "update", "delete"],
    id: int,
    content: str | None = None
):
    """Manage memories.

    Args:
        action (str): The action to perform. Can be one of "create", "update", or "delete".
        id (int): The id of the memory.
        content (str): The content of the memory. Only required when action is "create" or "update".

    Returns:
        The updated memories.
    """
    global memories
    if action == "create":
        memories[id] = content
    elif action == "update":
        if id not in memories:
            raise ValueError(f"Memory with id {id} does not exist.")
        if content is None:
            raise ValueError(
                f"Content cannot be None when updating memory with id {id}."
            )
        memories[id] = content
    elif action == "delete":
        if id not in memories:
            raise ValueError(f"Memory with id {id} does not exist.")
        del memories[id]
    return memories


def get_memories():
    """Get all memories.

    Returns:
        The memories.
    """
    return memories


# 메모리 함수 동작 테스트
manage_memories(action="create", id=1, content="The user's name is Kenny.")
print("\n[테스트] 메모리 생성:", memories)

manage_memories(action="update", id=1, content="The user's name is Bob.")
print("[테스트] 메모리 수정:", memories)

manage_memories(action="delete", id=1)
print("[테스트] 메모리 삭제:", memories)


##########################################
# Part 2. 첫 번째 대화 - 새 정보 기억
##########################################
# 사용자가 새로운 정보를 알려주면, 모델이 manage_memories 도구 호출을 요청함.
# 이 시점에서는 tool calling 루프를 따라 실제로 함수를 실행하고
# 결과를 다시 모델에 전달해야 하지만, 여기서는 요청만 확인함.

# 도구 스키마 정의
tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="manage_memories",
            description="Create, update, or delete memories.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "action": types.Schema(
                        type=types.Type.STRING,
                        description="The action to perform. Can be one of 'create', 'update', or 'delete'.",
                    ),
                    "id": types.Schema(
                        type=types.Type.INTEGER,
                        description="The id of the memory.",
                    ),
                    "content": types.Schema(
                        type=types.Type.STRING,
                        description="The content of the memory. Only required when action is 'create' or 'update'.",
                    ),
                },
                required=["action", "id"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_memories",
            description="Get all memories.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
            ),
        ),
    ]
)

SYSTEM_INSTRUCTION = (
    "Your name is Aura. You are a personal assistant and your job is to help the user with general tasks, "
    "questions, and requests. In order to perform your job well, you need to keep track of important information "
    "about the user. You have access to a tool called `manage_memories` that allows you to create, update, or "
    "delete memories. Use this tool to keep track of important personal information about the user. Examples of "
    "important information includes, but is not limited to, personal details, work-related details, personal "
    "preferences, relationships, and goals. Every time you learn new information about the user, you should "
    "create a new memory. You also have access to a tool called `get_memories` that allows you to retrieve all "
    "memories. You should always use this tool to retrieve all memories which may have important context, "
    "before responding to the user."
)

contents = [
    types.Content(
        role="user",
        parts=[types.Part(text="Remember that my name is Kenny and my wife's name is Nancy.")],
    ),
]

config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[tools],
)

response = client.models.generate_content(
    model=MODEL,
    contents=contents,
    config=config,
)

# 모델이 manage_memories 도구 호출을 요청한 것을 확인
# 실제 tool calling 루프(함수 실행 → 결과 전달 → 최종 답변)는 2_tool_calling.py 참고
print("\n[Part 2] 첫 번째 대화 - 모델의 도구 호출 요청:")
print(response.candidates[0].content)


##########################################
# Part 3. 두 번째 대화 - 기억 불러오기
##########################################
# 새 대화가 시작됐지만, 메모리 저장소(memories dict)에는 정보가 남아 있음.
# 모델이 get_memories를 먼저 호출해서 과거 정보를 확인한 뒤 답변하는 것을 볼 수 있음.

# 에이전트가 이전 대화에서 메모리를 저장했다고 가정
manage_memories(action="create", id=1, content="The user's name is Kenny.")
manage_memories(action="create", id=2, content="Kenny's wife's name is Nancy.")
# 이전 대화 기록은 전달하지 않고 새로운 대화 시작
question = "Do you remember my wife's name?"

# Python 함수를 직접 등록하면 SDK가
# 도구 호출 → 함수 실행 → 결과 전달 → 최종 답변 생성을 자동 처리
memory_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[manage_memories, get_memories],
)

response = client.models.generate_content(
    model=MODEL,
    contents=question,
    config=memory_config,
)

print("\n[Part 3] 모델의 최종 답변:")
print(response.text)
