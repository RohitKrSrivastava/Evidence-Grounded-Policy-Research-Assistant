"""Interactive and scriptable Command-Line Interface (CLI) for the Evidence-Grounded Policy Assistant."""
import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.agent.workflow import PolicyAgentWorkflow
from src.evaluation.runner import BenchmarkRunner
from src.mcp.client import PolicyMCPClient
from src.mcp.server import PolicyMCPServer

console = Console()

def run_query(query: str):
    """Executes a policy query and renders rich output."""
    workflow = PolicyAgentWorkflow()
    console.print(Panel(f"[bold cyan]Policy Research Query:[/bold cyan] {query}", expand=False))
    answer, state = workflow.run(query)

    console.print(Panel(answer.direct_answer, title="[bold green]Policy Assistant Synthesis[/bold green]", expand=False))

    if answer.citations:
        t_cit = Table(title="Traceable Citations & Evidence Passages", show_header=True, header_style="bold magenta")
        t_cit.add_column("Doc ID", style="cyan", width=18)
        t_cit.add_column("Section", style="green", width=25)
        t_cit.add_column("Verbatim Quote", style="white")
        for c in answer.citations:
            t_cit.add_row(c.source_id, c.section[:24], f"\"{c.quote[:100]}...\"")
        console.print(t_cit)

    if answer.calculations:
        t_calc = Table(title="Deterministic Arithmetic Audit Trail", show_header=True, header_style="bold yellow")
        t_calc.add_column("Operation", style="cyan")
        t_calc.add_column("Expression", style="white")
        t_calc.add_column("Inputs", style="dim")
        t_calc.add_column("Verified Result", style="bold green")
        for calc in answer.calculations:
            t_calc.add_row(calc.operation, calc.expression, str(calc.inputs), calc.formatted_result)
        console.print(t_calc)

    if answer.conflict_analysis and answer.conflict_analysis.has_conflict:
        console.print(Panel(
            f"[bold]Perspective A ({answer.conflict_analysis.source_a}):[/bold] {answer.conflict_analysis.claim_a}\n"
            f"[bold]Perspective B ({answer.conflict_analysis.source_b}):[/bold] {answer.conflict_analysis.claim_b}\n\n"
            f"[bold yellow]Reconciliation Guidance:[/bold yellow] {answer.conflict_analysis.reconciliation_guidance}",
            title="[bold red]Contradictory Empirical Projections Reconciled[/bold red]",
            border_style="red"
        ))

    console.print(
        f"[dim]Telemetry: Latency: {answer.latency_ms:.1f}ms | Uncertainty: {answer.uncertainty_level.value} | "
        f"Guardrails: {'PASSED' if answer.guardrails_passed else 'REJECTED'}[/dim]\n"
    )

def main():
    parser = argparse.ArgumentParser(description="Evidence-Grounded Policy Research Assistant CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Query command
    q_parser = subparsers.add_parser("query", help="Ask a single policy research question")
    q_parser.add_argument("query_text", type=str, help="The question string")

    # Benchmark command
    subparsers.add_parser("benchmark", help="Run full 35-case benchmark comparing Baseline vs Advanced RAG")

    # Demo command
    subparsers.add_parser("demo", help="Run all 10 Minimum Demonstration Scenarios")

    # MCP discover command
    subparsers.add_parser("mcp-discover", help="Discover tools and resources on the local MCP server")

    args = parser.parse_args()

    if args.command == "query":
        run_query(args.query_text)
    elif args.command == "benchmark":
        console.print("[bold cyan]Running 35-case benchmark evaluation...[/bold cyan]")
        runner = BenchmarkRunner()
        res = runner.run_full_benchmark()
        console.print("[bold green]Benchmark evaluation completed! Saved to data/processed/benchmark_comparison_results.json[/bold green]")
        console.print("Baseline Summary:", res["comparison"]["Config_A_Baseline"])
        console.print("Advanced RAG Summary:", res["comparison"]["Config_B_Advanced_RAG"])
    elif args.command == "demo":
        from run_scenarios import run_all_scenarios
        run_all_scenarios()
    elif args.command == "mcp-discover":
        client = PolicyMCPClient()
        caps = client.discover_capabilities()
        console.print("[bold green]Discovered MCP Capabilities:[/bold green]", caps)
    else:
        # Default interactive prompt
        console.print("[bold cyan]Interactive Policy Research Assistant CLI (type 'exit' or 'quit' to close)[/bold cyan]")
        while True:
            try:
                user_q = console.input("[bold yellow]Policy Query > [/bold yellow]").strip()
                if user_q.lower() in ("exit", "quit", "q"):
                    break
                if user_q:
                    run_query(user_q)
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == "__main__":
    main()
