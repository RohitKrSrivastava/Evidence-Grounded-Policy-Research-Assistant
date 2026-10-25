"""Lightweight FastAPI application for Evidence-Grounded Policy Research Assistant."""
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from src.schema import PolicyAnswer
from src.agent.workflow import PolicyAgentWorkflow
from src.evaluation.runner import BenchmarkRunner
from src.mcp.client import PolicyMCPClient
from src.config import CONFIG

app = FastAPI(
    title="Evidence-Grounded Policy Research Assistant API",
    description="Production-ready GenAI API for policy analysts, with traceable citations, deterministic arithmetic, and responsible AI guardrails.",
    version="1.0.0"
)

workflow = PolicyAgentWorkflow()
mcp_client = PolicyMCPClient()

class QueryRequest(BaseModel):
    query: str = Field(description="Policy research question or analytical query", example="What was Singapore's ICM Value Added in 2023?")
    simulate_tool_retry: bool = Field(default=False, description="Simulate flaky tool failure to test retry mechanism")

@app.get("/health")
def health_check():
    """Returns system health, corpus size, and config summary."""
    return {
        "status": "HEALTHY",
        "service": "Singapore Policy Research Assistant",
        "corpus_chunks": len(workflow.corpus_chunks),
        "random_seed": CONFIG.model.random_seed,
        "mcp_initialized": mcp_client.is_initialized
    }

@app.post("/query", response_model=PolicyAnswer)
def process_policy_query(req: QueryRequest):
    """Processes analytical policy query through the bounded agent workflow."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    answer, state = workflow.run(req.query, simulate_flaky_tool=req.simulate_tool_retry)
    return answer

@app.get("/benchmark")
def get_benchmark_results():
    """Runs or retrieves the 35-case controlled benchmark comparison."""
    runner = BenchmarkRunner()
    results = runner.run_full_benchmark()
    return results

@app.get("/mcp/capabilities")
def get_mcp_capabilities():
    """Discovers MCP tools and resources."""
    return mcp_client.discover_capabilities()

@app.post("/mcp/call")
def call_mcp_tool(tool_name: str, arguments: Dict[str, Any] = Body(...)):
    """Invokes an MCP tool capability."""
    res = mcp_client.call_tool(tool_name, arguments)
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)
