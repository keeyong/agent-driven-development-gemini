# Agent With MCP

`agent_from_scratch`의 고객 서비스 에이전트를 MCP(Model Context Protocol) 방식으로 재구성한 버전입니다.

## agent_from_scratch와의 핵심 차이

| | agent_from_scratch/6_agent.py | agent_with_mcp/main.py |
|---|---|---|
| **도구 위치** | 에이전트 코드 안에 직접 정의 | MCP 서버로 분리 |
| **도구 추가** | 에이전트 코드 수정 필요 | mcp_config.json에 서버만 추가 |
| **재사용성** | 해당 에이전트에서만 사용 | 다른 에이전트/앱에서도 공유 가능 |
| **배포** | 단일 프로세스 | 서버별 독립 배포 가능 |

## 폴더 구조

```
agent_with_mcp/
├── main.py                  # 메인 에이전트 루프
├── mcp_config.json          # MCP 서버 연결 설정
├── 1_mcp_client_demo.py     # MCP 클라이언트 기능 데모
├── crm_db/
│   └── crm.json             # 고객 및 구매 이력 데이터
└── tools/
    ├── memory_mcp.py        # 메모리 관리 MCP 서버 (STDIO)
    ├── retrieval_mcp.py     # 검색 및 고객 분석 MCP 서버 (HTTP)
    └── tools.py             # 로컬 도구 (search_web)
```

## MCP 서버 구성

### memory_mcp.py (STDIO 방식)
- main.py 실행 시 **자동으로 자식 프로세스로 실행**됨. 별도 실행 불필요.
- **도구**: `manage_memories`, `get_memories`

### retrieval_mcp.py (HTTP 방식)
- **main.py 실행 전에 별도 터미널에서 먼저 실행 필요**
- **도구**: `search_products`, `search_faq`
- **리소스**: `status://last_updated`, `user://profile/{user_id}`
- **프롬프트**: `analyze_customer` (고객 구매 이력 분석)

## 실행 방법

**터미널 1** — retrieval MCP 서버 실행:
```bash
cd ai_launchpad/agents_module/agent_with_mcp
uv run python tools/retrieval_mcp.py
```

**터미널 2** — 에이전트 실행:
```bash
cd ai_launchpad/agents_module/agent_with_mcp
uv run python main.py
```

## MCP의 세 가지 기능

| 기능 | 설명 | 예시 |
|---|---|---|
| **Tool** | 함수 호출 (부작용 있음) | search_products, manage_memories |
| **Resource** | 읽기 전용 데이터 | user://profile/1, status://last_updated |
| **Prompt** | 프롬프트 템플릿 생성 | analyze_customer |

## 원격 배포

retrieval_mcp.py는 HTTP 방식이므로 서버에 배포 후 URL만 변경하면 어디서나 연결 가능합니다:

```json
// mcp_config.json
{
    "mcpServers": {
        "retrieval": {
            "url": "https://my-retrieval-server.com/mcp"  // 배포된 서버 URL로 변경
        }
    }
}
```

## 참고 자료

- [MCP 공식 문서](https://modelcontextprotocol.io/docs/getting-started/intro)
- [FastMCP 문서](https://gofastmcp.com/getting-started/welcome)
- [FastMCP 클라이언트 설정](https://gofastmcp.com/clients/client)
