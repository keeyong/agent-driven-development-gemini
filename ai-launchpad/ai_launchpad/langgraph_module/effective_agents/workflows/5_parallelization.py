"""
병렬화 (Parallelization) — 독립적인 작업을 동시에 실행

여러 독립적인 작업을 병렬로 실행해서 전체 처리 시간을 줄이는 패턴입니다.

예제: LinkedIn 포스트 생성 워크플로우
    START ──┬── generate_post     (포스트 텍스트 생성)
            ├── generate_image_prompt → generate_image → save_image  (이미지 생성)
            └── generate_hashtags (해시태그 생성)
            └──────────────────── create_preview (HTML 미리보기 생성)

세 가지 작업이 동시에 시작되고, 모두 완료되면 미리보기를 생성합니다.

## 핵심 개념
1. 지연 시간 감소: 독립적인 작업을 병렬로 실행해서 전체 처리 시간을 단축합니다.
2. 너비(Breadth): 여러 각도에서 동시에 접근해 더 풍부한 결과를 얻을 수 있습니다.
3. 이미지 생성: Google Imagen API를 사용해 Gemini와 함께 이미지 생성 (dall-e-3 대체)

⚠️  주의: 이미지 생성(Imagen)은 별도 API 활성화가 필요할 수 있습니다.
    이미지 생성 실패 시 텍스트만으로 미리보기를 생성합니다.

## 실행 방법
    uv run python workflows/5_parallelization.py
"""
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import Annotated
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, add_messages, END, START
from PIL import Image as PILImage
from io import BytesIO
import requests
import os

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemma-4-31b-it",
    temperature=0.1,
)

print("=" * 50)
print("  📌 병렬화: LinkedIn 포스트 + 이미지 + 해시태그")
print("  세 가지 작업이 동시에 실행됩니다")
print("=" * 50)


#################################
# State
#################################

class WorkflowState(BaseModel):
    """병렬 워크플로우 상태"""
    messages: Annotated[list, add_messages] = []
    image_prompt: str | None = None      # 이미지 생성용 프롬프트
    image_url: str | None = None         # 생성된 이미지 URL
    image_data: bytes | None = None      # 이미지 바이너리
    image_filename: str | None = None    # 저장된 파일명
    post: str | None = None              # 포스트 텍스트
    hashtags: str | None = None          # 해시태그


#################################
# 병렬 작업 1: 포스트 텍스트 생성
#################################

def generate_post(state: WorkflowState):
    """LinkedIn 포스트 텍스트 생성 (병렬 실행)"""
    print("\n[병렬 1] 포스트 텍스트 생성 중...")
    system_prompt = SystemMessage(content="""
    You are a LinkedIn content creator specializing in AI topics.

    Requirements:
    - 150-300 words
    - Conversational, professional tone
    - Start with a hook
    - Short 1-2 sentence paragraphs
    - End with a call-to-action
    - No title

    Respond with post text only.
    """)
    response = llm.invoke([system_prompt] + state.messages)
    print(f"✅ 포스트 텍스트 완료 ({len(response.content)}자)")
    return {"post": response.content}


#################################
# 병렬 작업 2: 이미지 생성 (프롬프트 → 이미지 → 저장)
#################################

def generate_image_prompt(state: WorkflowState):
    """이미지 생성을 위한 최적화된 프롬프트 생성 (병렬 실행)"""
    print("\n[병렬 2] 이미지 프롬프트 생성 중...")
    last_message = state.messages[-1]
    context = last_message.content if isinstance(last_message, HumanMessage) else ""

    prompt = HumanMessage(content=f"""
    Create a professional LinkedIn image prompt for this topic:

    Topic: {context}

    Requirements:
    - Clean, modern, professional aesthetic
    - No text in the image
    - Works well as a LinkedIn thumbnail
    - Maximum 400 characters

    Respond with the image prompt only.
    """)
    response = llm.invoke([prompt])
    print(f"✅ 이미지 프롬프트 생성 완료")
    return {"image_prompt": response.content}

def generate_image(state: WorkflowState):
    """이미지 프롬프트로 실제 이미지 생성"""
    print("\n[이미지] 생성 중...")
    if not state.image_prompt:
        return {}

    try:
        # Google Gemini의 이미지 생성 API 사용
        import google.generativeai as genai
        genai_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        response = genai_client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=state.image_prompt,
            config={"number_of_images": 1}
        )

        if response.generated_images:
            image_data = response.generated_images[0].image.image_bytes
            print("✅ 이미지 생성 완료")
            return {"image_data": image_data, "image_url": "generated_locally"}
        else:
            print("⚠️  이미지 생성 결과 없음, 건너뜁니다")
            return {}
    except Exception as e:
        print(f"⚠️  이미지 생성 실패 ({e}), 텍스트만으로 미리보기를 생성합니다")
        return {}

def save_image(state: WorkflowState):
    """생성된 이미지를 파일로 저장"""
    if state.image_data:
        image = PILImage.open(BytesIO(state.image_data))
        filename = "generated_image.png"
        image.save(filename)
        print(f"✅ 이미지 저장 완료: {filename}")
        return {"image_filename": filename}
    return {}


#################################
# 병렬 작업 3: 해시태그 생성
#################################

def generate_hashtags(state: WorkflowState):
    """관련 해시태그 생성 (병렬 실행)"""
    print("\n[병렬 3] 해시태그 생성 중...")
    last_message = state.messages[-1]
    context = last_message.content if isinstance(last_message, HumanMessage) else ""

    prompt = HumanMessage(content=f"""
    Generate 3 relevant LinkedIn hashtags for this topic: {context}

    Requirements:
    - Popular and relevant
    - 1-3 hashtags only

    Respond with hashtags only (e.g. #AI #Technology #Innovation).
    """)
    response = llm.invoke([prompt])
    print(f"✅ 해시태그 생성 완료: {response.content}")
    return {"hashtags": response.content}


#################################
# 결과 합치기: HTML 미리보기 생성
#################################

def create_preview(state: WorkflowState):
    """포스트 + 이미지 + 해시태그를 합쳐서 HTML 미리보기 생성"""
    print("\n[합치기] HTML 미리보기 생성 중...")
    try:
        hashtags = [h for h in (state.hashtags or "").split(" ") if h.startswith("#")]

        # 이미지 소스 결정
        img_src = state.image_filename or state.image_url or ""
        img_tag = f'<img src="{img_src}" alt="Cover image" class="cover-image">' if img_src else ""

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Post Preview</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 600px; margin: 20px auto; padding: 20px; }}
        .cover-image {{ width: 100%; border-radius: 8px; margin-bottom: 20px; }}
        .post-text {{ font-size: 16px; color: #333; white-space: pre-wrap; margin-bottom: 20px; }}
        .hashtags {{ font-size: 15px; color: #0073b1; }}
        .hashtag {{ margin-right: 8px; }}
    </style>
</head>
<body>
    {img_tag}
    <div class="post-text">{state.post}</div>
    <div class="hashtags">{"".join(f'<span class="hashtag">{h}</span>' for h in hashtags)}</div>
</body>
</html>"""

        with open("post_preview.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        print("✅ HTML 미리보기 저장: post_preview.html")
        return {"messages": [AIMessage(content="Preview created: post_preview.html")]}
    except Exception as e:
        print(f"❌ 미리보기 생성 실패: {e}")
        return {}


#################################
# 그래프 구성 — 병렬 실행
#################################

builder = StateGraph(WorkflowState)

builder.add_node(generate_post)
builder.add_node(generate_image_prompt)
builder.add_node(generate_image)
builder.add_node(save_image)
builder.add_node(generate_hashtags)
builder.add_node(create_preview)

# START에서 3개 노드가 동시에 시작됨 (병렬)
builder.add_edge(START, "generate_post")
builder.add_edge(START, "generate_image_prompt")
builder.add_edge(START, "generate_hashtags")

# 이미지 체인: 프롬프트 → 생성 → 저장
builder.add_edge("generate_image_prompt", "generate_image")
builder.add_edge("generate_image", "save_image")

# 세 갈래가 모두 create_preview로 합쳐짐
builder.add_edge("save_image", "create_preview")
builder.add_edge("generate_post", "create_preview")
builder.add_edge("generate_hashtags", "create_preview")

builder.add_edge("create_preview", END)

graph = builder.compile()

# 실행
topic = "Most AI integrations fail because of overcomplication. AI workflows solve most problems with more reliability and control."
print(f"\n주제: {topic}")

response = graph.invoke(WorkflowState(messages=[topic]))

print("\n" + "=" * 50)
print("  📄 최종 결과")
print("=" * 50)
print(f"\n[포스트]\n{response['post']}")
print(f"\n[해시태그] {response['hashtags']}")
print(f"\n[이미지 프롬프트] {response['image_prompt']}")
