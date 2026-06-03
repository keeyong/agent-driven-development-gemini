"""
로컬 도구 정의

MCP 서버로 분리하지 않고 에이전트 코드에 직접 포함된 도구들.
주로 외부 API를 호출하는 간단한 도구들이 여기에 정의됩니다.
"""
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


def search_web(query: str):
    """Search the web and get back a list of search results including the page title, url, and the cleaned content of each webpage.

    Args:
        query: The search query.

    Returns:
        A dictionary of the search results.
    """
    tavily_client = TavilyClient()
    response = tavily_client.search(query, max_results=3)
    return response
