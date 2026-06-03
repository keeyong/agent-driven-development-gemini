"""
멀티 에이전트 슈퍼바이저 실행 진입점

Rich 라이브러리로 각 에이전트의 출력을 색상 구분된 패널로 스트리밍합니다.

    🎯 Supervisor  — 초록색 패널
    🔬 Researcher  — 청록색 패널
    ✍️  Copywriter — 마젠타 패널

## 실행 방법
    # 프로젝트 루트에서
    uv run python -m ai_launchpad.langgraph_module.multi_agent.supervisor.main

    # 또는
    cd ai_launchpad/langgraph_module/multi_agent/supervisor
    uv run python main.py
"""
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langgraph.types import RunnableConfig
from ai_launchpad.langgraph_module.multi_agent.supervisor.supervisor import graph as supervisor_graph, SupervisorState
from langchain_core.messages import HumanMessage, AIMessageChunk
from rich.console import Console
from rich.panel import Panel


load_dotenv()

def get_responsive_width(console: Console) -> int:
    """Get responsive width with margins for panels."""
    return min(120, console.size.width - 4) if console.size.width > 10 else 80

async def stream_graph_responses(
        input: SupervisorState,
        graph: StateGraph,
        console: Console,
        **kwargs
        ):
    """Asynchronously stream the result of the graph run with subgraph support.

    Args:
        input: The input to the graph.
        graph: The compiled graph.
        console: Rich console for output.
        **kwargs: Additional keyword arguments.

    Returns:
        str: The final LLM or tool call response
    """
    # Agent styling configuration
    AGENT_STYLES = {
        'researcher': {'color': 'cyan', 'emoji': '🔬', 'name': 'Researcher'},
        'copywriter': {'color': 'magenta', 'emoji': '✍️', 'name': 'Copywriter'},
        'supervisor': {'color': 'green', 'emoji': '🎯', 'name': 'Supervisor'},
    }

    # Track current AI message source to detect transitions
    current_ai_source = None
    current_content = ""
    current_tool_args = ""
    current_tool_name = ""

    async for chunk in graph.astream(
        input=input,
        stream_mode="messages",
        subgraphs=True,
        **kwargs
        ):
        # When subgraphs=True, the structure is (namespace, (message_chunk, metadata))
        namespace, (message_chunk, _) = chunk

        if isinstance(message_chunk, AIMessageChunk):
            # Determine the source of this AI message directly from namespace
            if namespace:
                # This is from a subgraph - detect agent from namespace
                namespace_str = str(namespace)
                if "call_researcher" in namespace_str:
                    ai_source = "researcher"
                elif "call_copywriter" in namespace_str:
                    ai_source = "copywriter"
                else:
                    # Fallback for unknown subgraphs
                    ai_source = "researcher"
            else:
                # This is from the main graph (supervisor)
                ai_source = "supervisor"

            # Check if we're transitioning between different AI sources
            if current_ai_source != ai_source:
                # Finalize previous agent's content in a panel
                if current_content.strip() and current_ai_source:
                    style = AGENT_STYLES[current_ai_source]
                    panel = Panel(
                        current_content.strip(),
                        title=f"{style['emoji']} {style['name']}",
                        border_style=style['color'],
                        title_align="left",
                        padding=(1, 2),
                        width=get_responsive_width(console)
                    )
                    console.print(panel)
                    console.print()  # Add spacing after completed panel

                # Start new agent
                current_ai_source = ai_source
                current_content = ""
            elif current_ai_source is None:
                # First AI message
                current_ai_source = ai_source
                current_content = ""

            # Handle tool calls
            if message_chunk.response_metadata:
                finish_reason = message_chunk.response_metadata.get("finish_reason", "")
                if finish_reason == "tool_calls":
                    # Print accumulated tool args if we have them
                    if current_tool_args.strip():
                        if current_ai_source:
                            style = AGENT_STYLES[current_ai_source]
                            console.print(f"  [dim {style['color']}]{current_tool_args.strip()}[/dim {style['color']}]")
                        else:
                            console.print(f"  [dim]{current_tool_args.strip()}[/dim]")
                        current_tool_args = ""
                    console.print("  🔧 [yellow]Tool call completed[/yellow]")
                    console.print()  # Add spacing after tool completion

            if message_chunk.tool_call_chunks:
                tool_chunk = message_chunk.tool_call_chunks[0]
                tool_name = tool_chunk.get("name", "")
                args = tool_chunk.get("args", "")

                if tool_name and tool_name != current_tool_name:
                    # New tool call - print the name
                    console.print(f"  🔧 [yellow]TOOL CALL: {tool_name}[/yellow]")
                    current_tool_name = tool_name
                    current_tool_args = ""  # Reset args for new tool

                if args:
                    # Accumulate args instead of printing immediately
                    current_tool_args += args
            else:
                # Just accumulate content for panel display
                if message_chunk.content:
                    current_content += message_chunk.content
        else:
            # Handle other message types
            pass

    # Print any remaining tool args
    if current_tool_args.strip():
        if current_ai_source:
            style = AGENT_STYLES[current_ai_source]
            console.print(f"  [dim {style['color']}]{current_tool_args.strip()}[/dim {style['color']}]")
        else:
            console.print(f"  [dim]{current_tool_args.strip()}[/dim]")
        console.print()

    # Finalize the last agent's content in a panel
    if current_content.strip() and current_ai_source:
        style = AGENT_STYLES[current_ai_source]
        panel = Panel(
            current_content.strip(),
            title=f"{style['emoji']} {style['name']}",
            border_style=style['color'],
            title_align="left",
            padding=(1, 2),
            width=get_responsive_width(console)
        )
        console.print(panel)
        console.print()  # Add spacing after final panel


async def main():
    """멀티 에이전트 슈퍼바이저 실행.

    Supervisor → Researcher(s) → Copywriter 순서로 작업을 조율합니다.
    Rich 라이브러리로 각 에이전트의 출력을 색상 구분된 패널로 표시합니다.
    """
    console = Console()

    try:
        config = RunnableConfig(configurable={
            "thread_id": "1",
            "recursion_limit": 50,
        })

        # Welcome panel with responsive width
        welcome_panel = Panel(
            "[bold]멀티 에이전트 슈퍼바이저[/bold]\n\n"
            "🎯 [green]Supervisor[/green]  — 계획 수립 및 작업 위임\n"
            "🔬 [cyan]Researcher[/cyan]  — 웹 검색 및 리서치 보고서 생성\n"
            "✍️  [magenta]Copywriter[/magenta] — 보고서 기반 콘텐츠 작성\n\n"
            "[dim]예시: 'Write a LinkedIn post about how AI is changing software development'\n"
            "종료: 'exit' 또는 'quit'[/dim]",
            title="🚀 AI Launchpad — Multi-Agent Supervisor",
            border_style="blue",
            title_align="center",
            padding=(1, 2),  # Add padding to welcome panel
            width=get_responsive_width(console)
        )
        console.print(welcome_panel)
        console.print()  # Add spacing after welcome

        while True:
            console.print()
            user_input = console.input("[bold blue]User:[/bold blue] ")
            console.print()  # Add spacing after user input

            if user_input.lower() in ["exit", "quit"]:
                console.print("\n[yellow]Exit command received. Goodbye! 👋[/yellow]\n")
                break

            graph_input = SupervisorState(
                messages=[HumanMessage(content=user_input)]
            )

            await stream_graph_responses(graph_input, supervisor_graph, console, config=config)

    except Exception as e:
        console.print(f"[red]Error: {type(e).__name__}: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())


# ─── 예시 요청 ────────────────────────────────────────────────────────────────
# Write a LinkedIn post about how AI agents are changing the way we work
#
# Write a blog post about the top AI tools for entrepreneurs with real-world
# examples and case studies. Include actual numbers and results.
#
# Write a LinkedIn post on how MCP (Model Context Protocol) is unlocking
# new possibilities for AI agents. Include practical examples.