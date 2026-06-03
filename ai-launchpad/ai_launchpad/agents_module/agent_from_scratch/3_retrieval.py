"""
Retrieval is the process of retrieving context to incorporate into an LLM or AI agent conversation.

There are many ways to implement retrieval. In this tutorial, we will cover the most common method which involves using a vector database. This example shows how we can give an agent access to a product database.

## Retrieval with Vector Databases
- Vector databases are a type of database that stores data as vectors.
- Vectors are a numerical representation of data. In the context of AI, vectors are typically used to represent text or images.
- Vector databases are used for similarity search. This means finding the most similar vectors to a given query vector.
- Chroma is a popular open-source vector database.

## 이 파일의 전체 흐름

이 파일은 LLM이 벡터 데이터베이스를 도구로 사용해 제품을 검색하는 방법을 다룹니다.

### 전체 구조

    [Part 1] 지식 베이스(Knowledge Base) 구축
             - 제품 설명 텍스트를 임베딩(숫자 벡터)으로 변환
             - ChromaDB에 저장
             - 유사도 검색 테스트

    [Part 2] LLM + 검색 도구 연결 (Retrieval)
             - search_products() 함수를 도구로 정의
             - 사용자 질문 → 모델이 search_products 호출 요청
             (실제 tool calling 루프는 2_tool_calling.py 참고)

핵심 포인트:
- 임베딩(Embedding): 텍스트를 숫자 벡터로 변환하는 과정. 의미가 비슷한 텍스트는 벡터 공간에서 가깝게 위치함.
- 유사도 검색: 사용자 질문을 벡터로 변환한 뒤, DB에서 가장 가까운 벡터(= 가장 관련 있는 문서)를 찾음.
- ChromaDB의 기본 임베딩 함수는 onnxruntime을 의존성으로 선언하는데, Intel Mac + Python 3.13에서는
  호환되는 wheel이 없어 설치 불가. 여기서는 Google Embedding API를 대신 사용해서 onnxruntime을 우회함.
"""
from google import genai
from google.genai import types
from dotenv import load_dotenv
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
import os

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemma-4-31b-it"


##########################################
# Part 1. 지식 베이스(Knowledge Base) 구축
##########################################

# ChromaDB는 기본 임베딩 함수의 의존성으로 onnxruntime을 선언하지만,
# Intel Mac + Python 3.13에서는 호환 wheel이 없어 설치 불가.
# 실제로 onnxruntime을 사용하지 않더라도 chromadb 패키지가 의존성으로 선언하기 때문에
# pyproject.toml의 override-dependencies로 Intel Mac에서만 설치를 스킵하고,
# 임베딩 함수는 Google Embedding API로 직접 구현해서 대체함.
class GoogleEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        pass

    def __call__(self, input: Documents) -> Embeddings:
        result = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=input,
        )
        # chromadb가 요구하는 형식: List[List[float]]
        return [e.values for e in result.embeddings]


chroma_client = chromadb.Client()

# 제품 데이터를 저장할 컬렉션 생성 (이미 있으면 가져옴)
collection = chroma_client.get_or_create_collection(
    name="products",
    embedding_function=GoogleEmbeddingFunction(),  # Google Embedding API 사용
)

# 제품 설명 텍스트를 DB에 저장
# upsert: 이미 같은 id가 있으면 업데이트, 없으면 삽입
collection.upsert(
    documents=[
        "SwiftStride Running Shorts: Engineered for peak performance, these lightweight running shorts feature a moisture-wicking fabric to keep you dry and comfortable. The built-in liner provides extra support, while a secure zippered back pocket is perfect for your keys or a small music device.",
        "AuraFlow Yoga Mat: Elevate your practice with the AuraFlow Yoga Mat. Its dual-sided non-slip surface offers superior grip and stability, allowing you to hold even the most challenging poses. Made from eco-friendly, high-density TPE material, it provides optimal cushioning for your joints.",
        "CoreFlex Training Hoodie: Stay warm without sacrificing mobility. The CoreFlex Training Hoodie is designed with a soft, breathable fleece that provides insulation while allowing for a full range of motion. Its athletic fit, thumbholes, and a three-panel hood offer comfort and a sleek look for your gym sessions or outdoor runs."
    ],
    ids=["1", "2", "3"]
)

# 유사도 검색 테스트: 질문과 가장 관련 있는 제품 1개 반환
results = collection.query(
    query_texts=["I just started running and I'm looking for some shorts."],
    n_results=1
)

print("\n[유사도 검색 테스트] 'I just started running and I'm looking for some shorts.'")
print(results)


##########################################
# Part 2. LLM + 검색 도구 연결 (Retrieval)
##########################################
# search_products()를 LLM이 사용할 수 있는 도구로 등록.
# 사용자 질문이 들어오면 LLM이 직접 답하지 않고 이 도구를 호출하도록 유도함.

def search_products(query: str, num_results: int = 3):
    """Search the product database and get back a list of products.

    Args:
        query: The search query.
        num_results: The number of results to return, max is 3.

    Returns:
        A dictionary of the search results.
    """
    results = collection.query(
        query_texts=[query],
        n_results=min(num_results, 3)
    )
    return results


# 모델에게 전달할 도구 스키마 정의
tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_products",
            description="Search the product database and get back a list of products.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="The search query.",
                    ),
                    "num_results": types.Schema(
                        type=types.Type.INTEGER,
                        description="The number of results to return, max is 3.",
                    ),
                },
                required=["query"],
            ),
        )
    ]
)

# 사용자 질문과 도구 목록을 함께 모델에 전달
contents = [
    types.Content(role="user", parts=[types.Part(text="I just started running and I'm looking for some shorts.")]),
]

config = types.GenerateContentConfig(
    system_instruction="Your name is Aura. You are a sales agent. You have access to a tool called `search_products` that allows you to search a product database. Do not rely on your own knowledge, always use the `search_products` tool to answer the user's questions.",
    tools=[tools],
)

response = client.models.generate_content(
    model=MODEL,
    contents=contents,
    config=config,
)

# 모델이 직접 답하지 않고 search_products 호출을 요청한 것을 확인할 수 있음.
# 실제 tool calling 루프(함수 실행 → 결과 전달 → 최종 답변)는 2_tool_calling.py 참고.
print("\n[모델의 도구 호출 요청]")
print(response.candidates[0].content)
