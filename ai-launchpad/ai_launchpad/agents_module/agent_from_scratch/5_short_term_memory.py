"""
Short-term memory can be thought of as the working memory of an agent within a single conversation. Typically this just means the conversation history.

## Agent Loops
- This is a simplified example just to show you the mechanics of cycling through a back-and-forth conversation. It's more of a chatbot and it can only respond so it doesn't really have agency yet.
- A complete agent loop will include tool calling: the agent will be able to take actions in its environment, perceive the results, and then decide what to do next. In other words, it will have agency.

See the `Agents` section for more information.
https://www.anthropic.com/engineering/building-effective-agents

## 이 파일의 전체 흐름

단기 기억(Short-term Memory)은 현재 대화 내에서의 기억입니다.
LLM은 stateless이기 때문에, 이전 메시지를 기억하려면 매 호출마다 전체 대화 히스토리를 함께 전달해야 합니다.

    while True:
        1. 사용자 입력 받기
        2. contents(대화 히스토리)에 추가
        3. 전체 히스토리를 모델에 전달 → 응답 생성
        4. 응답을 히스토리에 추가
        5. 반복 (exit/quit 입력 시 종료)

핵심 포인트:
- contents 리스트가 곧 단기 기억. 대화가 길어질수록 리스트가 커짐.
- 프로그램이 종료되면 contents도 사라짐 — 장기 기억이 필요하면 4_long_term_memory.py 참고.
- 아직 tool calling이 없으므로 진정한 의미의 에이전트는 아님. 다음 단계에서 추가됨.
"""
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-3.1-flash-lite"

config = types.GenerateContentConfig(
    system_instruction="Your name is Aura. You are a great friend and love banter. Always keep the conversation going and light-hearted.",
)

# 대화 히스토리 — 여기에 메시지가 쌓이는 것이 곧 단기 기억
contents = []

# 사용자와 에이전트가 번갈아 대화하는 루프
while True:
    user_input = input("\n\nUser: ")
    if user_input.lower() in ["exit", "quit"]:
        print("\n\nExit command received. Exiting...\n\n")
        break

    # 사용자 메시지를 히스토리에 추가
    contents.append(
        types.Content(role="user", parts=[types.Part(text=user_input)])
    )
    print(f"\n ----- 🥷 Human ----- \n\n{user_input}\n")

    # 전체 대화 히스토리를 모델에 전달 → 문맥을 유지한 채 응답 생성
    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=config,
    )

    # 모델 응답을 히스토리에 추가 (다음 호출 때 문맥으로 사용)
    contents.append(response.candidates[0].content)
    print(f"\n ----- 🤖 Assistant ----- \n\n{response.text}\n")
