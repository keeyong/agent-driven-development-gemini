"""
검색 및 고객 분석 MCP 서버 (HTTP 방식)

이 파일은 FastMCP를 사용해 제품/FAQ 검색과 고객 분석을 제공하는 MCP 서버를 정의합니다.
HTTP 방식으로 실행되므로 main.py 실행 전에 별도 터미널에서 먼저 실행해야 합니다.

실행 방법:
    uv run python tools/retrieval_mcp.py
    → http://127.0.0.1:8001/mcp 에서 서버 시작

제공하는 MCP 도구:
    - search_products: 제품 DB 검색
    - search_faq: FAQ DB 검색

제공하는 MCP 리소스 (읽기 전용 데이터):
    - status://last_updated: 지식 베이스 마지막 업데이트 날짜
    - user://profile/{user_id}: 고객 프로필 및 구매 이력

제공하는 MCP 프롬프트 (프롬프트 템플릿):
    - analyze_customer: 고객 구매 이력 기반 분석 프롬프트 생성

배포 시: mcp_config.json의 url을 배포된 서버 주소로 변경하면
어디서나 이 서버에 연결 가능합니다.
"""
from dotenv import load_dotenv
import json
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from typing import Literal, Dict, List, Any
import os
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from google import genai

load_dotenv()

# ChromaDB는 기본 임베딩 함수의 의존성으로 onnxruntime을 선언하지만,
# Intel Mac + Python 3.13에서는 호환 wheel이 없어 설치 불가.
# Google Embedding API로 직접 구현해서 대체함.
_genai_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

class GoogleEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        pass

    def __call__(self, input: Documents) -> Embeddings:
        result = _genai_client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=input,
        )
        return [e.values for e in result.embeddings]

embedding_fn = GoogleEmbeddingFunction()

# MCP 서버 생성. name은 클라이언트에서 도구를 구분할 때 prefix로 사용됨
# 예: search_products → retrieval_search_products
mcp = FastMCP(name="retrieval")


# 서버 상태 확인용 헬스체크 엔드포인트 (MCP 프로토콜 외 커스텀 HTTP 라우트)
# curl http://127.0.0.1:8001/health 로 서버 상태 확인 가능
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


##########################################
# 지식 베이스 구축 (ChromaDB)
##########################################
# agent_from_scratch의 knowledgebase/ 폴더에서 JSON 파일을 읽어 ChromaDB에 로드

chroma_client = chromadb.Client()

# 이 파일 기준으로 절대 경로 계산 (실행 위치와 무관하게 동작)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
knowledgebase_path = os.path.join(BASE_DIR, "../../agent_from_scratch/knowledgebase")

for collection in os.listdir(knowledgebase_path):
    collection_name = collection.split(".")[0]
    try:
        collection = chroma_client.get_or_create_collection(name=collection_name, embedding_function=embedding_fn)
        collection_data = json.load(open(f"{knowledgebase_path}/{collection_name}.json"))
        for item in collection_data:
            collection.upsert(
                documents=[json.dumps(item)],
                ids=[str(item["id"])],
                metadatas=[item["metadata"]],
            )
        print(f"[지식 베이스] '{collection_name}' 컬렉션 로드 완료 ({len(collection_data)}개)")
    except Exception as e:
        print(f"[지식 베이스] '{collection_name}' 로드 실패: {e}")


##########################################
# MCP 도구 정의
##########################################

@mcp.tool()
def search_products(
        query: str,
        gender: Literal["men", "women"] | None = None,
        category: Literal["running", "gym", "yoga"] | None = None,
        num_results: int = 3) -> List[Dict[str, Any]]:
    """Search the product database and get back a list of products.

    Args:
        query: The search query.
        gender: The gender of the product. Can be one of "men" or "women".
        category: The category of the product. Can be one of "running", "gym", or "yoga".
        num_results: The number of results to return, max is 3.

    Returns:
        A dictionary of the search results.
    """
    where = {}
    if gender and category:
        where["$and"] = [{"gender": gender}, {"category": category}]
    elif category:
        where["category"] = category
    elif gender:
        where["gender"] = gender

    col = chroma_client.get_or_create_collection(name="products", embedding_function=embedding_fn)
    results = col.query(
        query_texts=[query],
        n_results=min(num_results, 3),
        where=where if where else None,
    )
    if not results["ids"][0]:
        return "No matching products found."
    return [json.loads(doc) for doc in results["documents"][0]]


@mcp.tool()
def search_faq(
        query: str,
        category: Literal["returns", "shipping", "discounts", "products"] | None = None,
        num_results: int = 3) -> List[Dict[str, Any]]:
    """Search the FAQ database and get back a list of answers.

    Args:
        query: The search query.
        category: The category of the question. Can be one of "returns", "shipping", "discounts", or "products".
        num_results: The number of results to return, max is 3.

    Returns:
        A dictionary of the search results.
    """
    where = {}
    if category:
        where["category"] = category

    col = chroma_client.get_or_create_collection(name="faq", embedding_function=embedding_fn)
    results = col.query(
        query_texts=[query],
        n_results=min(num_results, 3),
        where=where if where else None,
    )
    if not results["ids"][0]:
        return "No matching answers found."
    return [json.loads(doc) for doc in results["documents"][0]]


##########################################
# MCP 리소스 정의 (읽기 전용 데이터)
##########################################
# 리소스는 GET 요청처럼 읽기 전용 데이터를 노출함
# 도구(tool)와 달리 부작용 없이 데이터를 조회하는 용도

@mcp.resource("status://last_updated")
def get_last_updated():
    """지식 베이스 마지막 업데이트 날짜를 반환합니다."""
    return "Last Updated: 2025-09-02"


##########################################
# 고객 프로파일링 및 분석
##########################################
# CRM DB(JSON 파일)에서 고객 데이터를 읽어 프로필을 구성
# 실제 서비스에서는 Postgres, Salesforce 등 실제 CRM과 연동

def _get_user_profile_data(user_id: int) -> Dict[str, Any]:
    """CRM DB에서 고객 프로필과 구매 이력을 조회하는 내부 함수."""
    try:
        crm_path = os.path.join(BASE_DIR, "../crm_db/crm.json")
        with open(crm_path, "r") as f:
            crm_data = json.load(f)

        users = crm_data["users"]
        transactions = crm_data["transactions"]

        user = next((user for user in users if user["id"] == user_id), None)
        if user is None:
            raise ValueError(f"User with id {user_id} does not exist.")

        past_purchases = [p for p in transactions if p["user_id"] == user_id][:5]

        return {
            "id": user_id,
            "name": user["name"],
            "age": user["age"],
            "gender": user["gender"],
            "location": user["location"],
            "total_purchases": len(past_purchases),
            "total_amount_spent": sum([p["price"] for p in past_purchases]),
            "average_purchase_amount": sum([p["price"] for p in past_purchases]) / len(past_purchases),
            "past_purchases": [
                {"id": p["id"], "name": p["name"], "price": p["price"], "category": p["category"]}
                for p in past_purchases
            ]
        }
    except Exception:
        raise ValueError(f"User with id {user_id} does not exist.")


@mcp.resource("user://profile/{user_id}")
def get_user_profile(user_id: int) -> Dict[str, Any]:
    """고객 프로필 및 구매 이력 리소스. user_id로 조회."""
    return _get_user_profile_data(user_id)


@mcp.prompt()
def analyze_customer(user_id: int) -> str:
    """
    고객 분석 프롬프트를 생성합니다.

    CRM DB에서 고객 프로필을 읽어 LLM이 분석할 수 있는 프롬프트 템플릿을 반환합니다.
    main.py에서 이 프롬프트를 LLM에 전달해 고객 인사이트를 생성합니다.
    """
    try:
        profile = _get_user_profile_data(user_id)
    except ValueError:
        raise ValueError(f"User with id {user_id} does not exist.")

    return f"""
    You are a sales agent for an athletic apparel company called FitFlex. You are analyzing a customer's profile to provide insights to the sales team.

    Here is the customer's profile:
    {json.dumps(profile)}

    Your goal is to provide insights about the customer that can help you provide a highly personalized experience for the customer.

    Insights should include but are not limited to:
    1. Most common purchased categories.
    2. Most common purchased products.
    3. Most likely preferred colors.
    4. Most likely purchase amount range (low, high).
    5. Categories of products the customer might be interested in but has not purchased yet.
    6. Any other insights you can provide.

    Provide insights about the customer.
    """


if __name__ == "__main__":
    # HTTP 방식으로 서버 실행
    # main.py 실행 전에 이 서버를 먼저 띄워야 함
    # 배포 시: host를 0.0.0.0으로 변경하고 원하는 포트 사용
    print("[retrieval MCP 서버] http://127.0.0.1:8001/mcp 에서 시작합니다...")
    mcp.run(transport="http", host="127.0.0.1", port=8001)
