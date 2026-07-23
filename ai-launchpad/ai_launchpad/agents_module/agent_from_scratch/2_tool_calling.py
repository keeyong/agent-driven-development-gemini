"""
Tools allow agents to take actions on the environment, retrieve additional context, and get feedback from the environment.

## Tool Calling with APIs
https://ai.google.dev/gemini-api/docs/function-calling

- Tool calling requires 5 total steps:
    1. Define the tool as a python function and send the function definition to the LLM model.
    2. The LLM calls the tool by returning a function_call response which includes the name of the tool and the arguments to pass to the tool.
    3. Parse the tool call arguments and execute the function.
    4. Send the tool output back to the LLM.
    5. The LLM returns a final response.

    See the guide above for a great illustration of this process.

- Some LLM providers like Google are introducing built-in tools which they implement and manage for you. We'll cover both here.

## 이 파일의 전체 흐름

이 파일은 LLM이 도구(Tool)를 사용하는 두 가지 방식을 다룹니다.

### Part 1. 내장 도구 (Built-in Tools)
LLM 제공사가 직접 구현하고 관리하는 도구입니다.
우리는 도구를 활성화만 하면 되고, 실행은 제공사 서버에서 알아서 처리합니다.

    사용자 질문 → [Gemini + Google Search 활성화] → 자동 검색 후 답변 반환

### Part 2. 커스텀 도구 (Function Calling)
우리가 직접 함수를 정의하고 실행까지 담당하는 방식입니다.
LLM은 "어떤 함수를 어떤 인자로 불러야 할지"만 결정하고,
실제 함수 실행과 결과 전달은 우리 코드가 담당합니다.

    [Step 1] search_web() 함수 정의 (실제 Tavily 검색 수행)
    [Step 2] 모델에게 전달할 도구 스키마 정의 (함수 이름/설명/파라미터)
    [Step 3] 사용자 질문 + 도구 목록을 모델에 전달
             → 모델이 답변 대신 "search_web('...')를 호출하라"는 요청을 반환
    [Step 4] 모델의 요청을 파싱해서 search_web() 직접 실행
             → 실행 결과를 대화 히스토리에 추가
    [Step 5] 검색 결과를 포함한 대화 히스토리를 모델에 다시 전달
             → 모델이 검색 결과를 바탕으로 최종 답변 생성

핵심 포인트:
- LLM은 함수를 직접 실행할 수 없음. "이 함수를 이 인자로 호출해줘"라고 요청할 뿐.
- 실제 실행은 항상 우리 Python 코드가 담당.
- 대화 히스토리(contents)에 모든 과정을 누적해서 모델이 문맥을 유지할 수 있게 함.
"""
from google import genai
from google.genai import types
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from datetime import date
import json
import os

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-3.1-flash-lite"
TODAY = date.today().isoformat()  # 예: "2026-06-01"

##########################################
# Built-in Tools (내장 도구)
##########################################
# Google이 직접 구현하고 관리하는 도구들.
# 우리가 함수를 정의하거나 실행할 필요 없이, 모델이 알아서 검색하고 결과를 반영함.
# 단, Google Search 내장 도구는 Gemini 모델에서만 지원되고 Gemma에서는 안 됨.

response = client.models.generate_content(
    model=MODEL,
    contents="What was one positive news story from today?",
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],  # 내장 Google 검색 도구 활성화
    ),
)
print("\n[내장 도구] 오늘의 긍정적인 뉴스:")
print(response.text)

# grounding_metadata: 모델이 어떤 웹페이지를 참고했는지 출처 정보
# 내장 검색을 사용했을 때만 제공됨
if response.candidates[0].grounding_metadata:
    print("\n[출처 정보]")
    print(response.candidates[0].grounding_metadata.grounding_chunks)


##########################################
# Function (Custom Tool) Calling (커스텀 도구 호출)
##########################################
# 내장 도구와 달리, 우리가 직접 함수를 정의하고 실행까지 담당하는 방식.
# LLM은 "어떤 함수를 어떤 인자로 호출해야 할지"만 결정하고,
# 실제 실행은 우리 코드(Python)가 담당함.
#
# 전체 흐름:
#   사용자 질문 → [모델] → 함수 호출 요청 → [우리 코드] 함수 실행
#   → 결과를 모델에 전달 → [모델] → 최종 답변

# Tavily: AI 에이전트용 웹 검색 API. 검색 결과를 LLM이 읽기 좋은 형태로 정제해서 반환함.
# https://github.com/tavily-ai/langchain-tavily


# Step 1. 실제로 실행할 Python 함수 정의
# ----------------------------------------
# 이 함수가 나중에 모델의 요청에 따라 실행될 실제 도구임.
def search_web(query: str):
    """Search the web and get back a list of search results including the page title, url, and the cleaned content of each webpage.

    Args:
        query: The search query.

    Returns:
        A dictionary of the search results.
    """
    tavily_search = TavilySearch(max_results=3, topic="general")
    response = tavily_search.invoke(input={"query": query})

    return response


# 함수가 제대로 동작하는지 직접 테스트
print("\n[Tavily 테스트] 'how to make a grilled cheese' 검색 결과:")
print(search_web("how to make a grilled cheese"))


# Step 2. 모델에게 알려줄 도구 스키마(설명서) 정의
# ----------------------------------------
# 모델은 Python 코드를 직접 볼 수 없으므로,
# 도구의 이름, 설명, 파라미터를 JSON 스키마 형태로 별도로 알려줘야 함.
# 모델은 이 설명을 보고 언제 어떻게 이 도구를 쓸지 판단함.
tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_web",
            description="Search the web and get back a list of search results including the page title, url, and the cleaned content of each webpage.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="The search query.",
                    ),
                },
                required=["query"],
            ),
        )
    ]
)


# Step 3. 도구 스키마와 함께 모델 호출
# ----------------------------------------
# 사용자 질문을 모델에게 보내면서, 사용할 수 있는 도구 목록도 함께 전달함.
# 모델은 질문을 보고 "검색이 필요하다"고 판단하면, 직접 답하지 않고
# search_web 함수를 어떤 인자로 호출해야 하는지를 응답으로 돌려줌.
contents = [
    types.Content(role="user", parts=[types.Part(text="What is the latest news about AI?")]),
]

config = types.GenerateContentConfig(
    system_instruction=f"Your name is Aura. You are a researcher. Today's date is {TODAY}. You have access to a tool called `search_web` that allows you to search the web. Do not rely on your own knowledge, always use the `search_web` tool to answer the user's questions.",
    tools=[tools],
)
response = client.models.generate_content(
    model=MODEL,
    contents=contents,
    config=config,
)
# 이 시점의 응답은 최종 답변이 아님.
# 모델이 "search_web('latest AI news')" 같은 함수 호출 요청을 담고 있음.
print("\n[Step 3] 모델의 함수 호출 요청:")
print(response.candidates[0].content)

# 모델의 함수 호출 요청을 대화 히스토리에 추가 (다음 호출 때 문맥으로 전달)
contents.append(response.candidates[0].content)


# Step 4. 함수 호출 요청을 파싱하고 실제로 실행
# ----------------------------------------
# 모델이 요청한 함수 이름과 인자를 꺼내서, 우리가 직접 함수를 실행함.
# 실행 결과를 다시 대화 히스토리에 추가해서 모델이 볼 수 있게 함.
function_call = None

for part in response.candidates[0].content.parts:
    if part.function_call:
        function_call = part.function_call  # 모델이 요청한 함수 호출 정보

# 모델이 요청한 인자로 실제 함수 실행
result = {"search_results": search_web(**dict(function_call.args))}

# 함수 실행 결과를 대화 히스토리에 추가
# function_call.name으로 어떤 함수의 결과인지 모델이 식별할 수 있음
contents.append(
    types.Content(
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    name=function_call.name,
                    response=result,
                )
            )
        ]
    )
)

print("\n[Step 4] 현재까지 대화 히스토리 (사용자 질문 → 함수 호출 요청 → 함수 실행 결과):")
for content in contents:
    print(content)
    print("\n-----\n")


# Step 5. 검색 결과를 포함해서 모델을 다시 호출 → 최종 답변 생성
# ----------------------------------------
# 이제 모델은 대화 히스토리를 통해 검색 결과를 볼 수 있음.
# 검색 결과를 바탕으로 사용자 질문에 대한 최종 답변을 생성함.
response = client.models.generate_content(
    model=MODEL,
    contents=contents,
    config=config,
)
print("\n[Step 5] 최종 답변:")
print(response.text)

# 최종 답변도 대화 히스토리에 추가
contents.append(response.candidates[0].content)

print("\n[전체 대화 흐름] 사용자 질문 → 함수 호출 → 검색 결과 → 최종 답변:")
for content in contents:
    print(content)
    print("\n-----\n")
