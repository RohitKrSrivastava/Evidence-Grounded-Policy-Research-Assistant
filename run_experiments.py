"""Experiment runner comparing Baseline (Config A) vs Advanced RAG (Config B) with statistical stratification."""
from rich.console import Console
from rich.table import Table
from src.evaluation.runner import BenchmarkRunner

console = Console()

def main():
    console.print("\n[bold cyan]Starting Controlled Empirical Evaluation Benchmark (35 cases)...[/bold cyan]\n")
    runner = BenchmarkRunner()
    results = runner.run_full_benchmark()

    # Render Overall Comparison Table
    table = Table(title="[bold yellow]Overall System Performance: Baseline vs Advanced Policy Assistant[/bold yellow]", show_header=True, header_style="bold cyan")
    table.add_column("Metric Dimension", style="bold white")
    table.add_column("Config A (Keyword Baseline)", style="red")
    table.add_column("Config B (Advanced RAG System)", style="green")
    table.add_column("Improvement / Delta", style="bold yellow")

    comp = results["comparison"]
    a = comp["Config_A_Baseline"]
    b = comp["Config_B_Advanced_RAG"]

    metrics_map = [
        ("Retrieval Recall@3", "mean_recall_at_3", "%"),
        ("Mean Reciprocal Rank (MRR)", "mean_mrr", "pts"),
        ("Retrieval nDCG@3", "mean_ndcg_at_3", "pts"),
        ("Factual Groundedness / Faithfulness", "mean_groundedness", "%"),
        ("End-to-End Task Accuracy", "mean_task_accuracy", "%"),
        ("Citation Precision", "mean_citation_precision", "%"),
        ("Mean Latency", "mean_latency_ms", "ms")
    ]

    for label, key, unit in metrics_map:
        val_a = a[key]
        val_b = b[key]
        delta = val_b - val_a
        delta_str = f"+{delta:.3f} {unit}" if delta > 0 else f"{delta:.3f} {unit}"
        table.add_row(label, f"{val_a:.3f}", f"{val_b:.3f}", delta_str)

    console.print(table)

    # Render Stratified Category Breakdown
    strat_table = Table(title="[bold yellow]Stratified Performance Across Case Categories (Config B)[/bold yellow]", show_header=True, header_style="bold magenta")
    strat_table.add_column("Category", style="cyan")
    strat_table.add_column("Recall@3", style="white")
    strat_table.add_column("Groundedness", style="green")
    strat_table.add_column("Task Accuracy", style="yellow")
    strat_table.add_column("Latency (ms)", style="dim")

    strat = results["stratified_results"]["Config_B_Advanced_RAG"]
    for cat, vals in strat.items():
        strat_table.add_row(
            cat.replace("_", " ").title(),
            str(vals["recall"]),
            str(vals["groundedness"]),
            str(vals["task_accuracy"]),
            str(vals["latency_ms"])
        )

    console.print(strat_table)
    console.print("\n[bold green]Experiment execution completed! Artifact saved to data/processed/benchmark_comparison_results.json[/bold green]\n")

if __name__ == "__main__":
    main()
