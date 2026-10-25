"""Model Context Protocol (MCP) Server exposing policy tools, resources, and prompts."""
import json
import math
from typing import Dict, Any, List, Optional
import pandas as pd
from src.config import STRUCTURED_DATA_DIR, UNSTRUCTURED_DATA_DIR

class PolicyMCPServer:
    """Standard Model Context Protocol Server providing policy data tools and resources."""

    SERVER_INFO = {
        "name": "SingaporePolicyResearchAssistant-MCP",
        "version": "1.0.0",
        "protocol_version": "2024-11-05"
    }

    TOOLS = [
        {
            "name": "query_policy_statistics",
            "description": "Queries macroeconomic digital economy statistics and workforce metrics.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "description": "Metric name to filter (e.g. 'Value Added', 'AI Adoption', 'Revenue')"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Optional four-digit year between 2018 and 2024"
                    }
                },
                "required": ["metric_name"]
            }
        },
        {
            "name": "calculate_growth_rate",
            "description": "Deterministically calculates Compound Annual Growth Rate (CAGR) or percentage change.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "start_val": {
                        "type": "number",
                        "description": "Starting base value (must be strictly positive)"
                    },
                    "end_val": {
                        "type": "number",
                        "description": "Ending period value (must be strictly positive)"
                    },
                    "num_years": {
                        "type": "number",
                        "description": "Number of intervening years (must be > 0)"
                    }
                },
                "required": ["start_val", "end_val", "num_years"]
            }
        },
        {
            "name": "verify_citation",
            "description": "Verifies whether a cited quote exists in authoritative policy source documents.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "quote": {
                        "type": "string",
                        "description": "Verbatim quote to verify"
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Authoritative document identifier (e.g. SG-DER-2024, SG-NAIS-2023)"
                    }
                },
                "required": ["quote", "doc_id"]
            }
        }
    ]

    RESOURCES = [
        {
            "uri": "policy://statistics/digital_economy_2024",
            "name": "Singapore Digital Economy Macro Indicators 2018-2023",
            "mimeType": "application/json",
            "description": "Official IMDA and SingStat time series on ICM Value Added, GDP share, and enterprise AI adoption."
        },
        {
            "uri": "policy://guidelines/ai_governance",
            "name": "IMDA / PDPC Advisory Guidelines on AI Recommendation Systems",
            "mimeType": "text/markdown",
            "description": "Regulatory guidance on consent, explainability, and human-in-the-loop safeguards."
        }
    ]

    PROMPTS = [
        {
            "name": "policy_synthesis_prompt",
            "description": "Standard prompt template for synthesizing cross-source evidence briefs.",
            "arguments": [
                {"name": "topic", "description": "Policy research domain", "required": True}
            ]
        }
    ]

    def __init__(self):
        self.macro_df = pd.read_csv(STRUCTURED_DATA_DIR / "sg_digital_economy_macro.csv")

    def handle_request(self, request_json: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches JSON-RPC 2.0 requests per MCP specification."""
        req_id = request_json.get("id")
        method = request_json.get("method")
        params = request_json.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": self.SERVER_INFO["protocol_version"],
                    "serverInfo": self.SERVER_INFO,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False}
                    }
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.TOOLS}
            }

        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"resources": self.RESOURCES}
            }

        elif method == "prompts/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"prompts": self.PROMPTS}
            }

        elif method == "tools/call":
            return self._handle_tool_call(req_id, params)

        elif method == "resources/read":
            return self._handle_resource_read(req_id, params)

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found."
                }
            }

    def _handle_tool_call(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "query_policy_statistics":
            metric = args.get("metric_name")
            if not metric or not isinstance(metric, str):
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Invalid params: 'metric_name' (string) is required."}
                }
            year = args.get("year")
            df = self.macro_df[self.macro_df["metric"].str.contains(metric, case=False, na=False)]
            if year:
                df = df[df["year"] == int(year)]
            records = df.to_dict(orient="records")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(records, indent=2)}],
                    "isError": False
                }
            }

        elif name == "calculate_growth_rate":
            try:
                start_val = float(args.get("start_val", 0))
                end_val = float(args.get("end_val", 0))
                num_years = float(args.get("num_years", 0))

                if start_val <= 0 or end_val <= 0 or num_years <= 0:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32602,
                            "message": "Validation Error: 'start_val', 'end_val', and 'num_years' must all be strictly positive numbers."
                        }
                    }

                cagr = (math.pow(end_val / start_val, 1.0 / num_years) - 1.0) * 100.0
                res = {
                    "operation": "CAGR",
                    "cagr_percent": round(cagr, 2),
                    "expression": f"(({end_val}/{start_val})**(1/{num_years}) - 1) * 100",
                    "formatted": f"{round(cagr, 2)}%"
                }
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(res)}],
                        "isError": False
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32603, "message": f"Calculation execution failure: {str(e)}"}
                }

        elif name == "verify_citation":
            quote = args.get("quote", "")
            doc_id = args.get("doc_id", "")
            if not quote or not doc_id:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": "Parameters 'quote' and 'doc_id' are required."}
                }

            # Check if quote exists in unstructured markdown documents
            verified = False
            for md_file in UNSTRUCTURED_DATA_DIR.glob("*.md"):
                text = md_file.read_text(encoding="utf-8")
                if doc_id.lower() in text.lower() and quote.lower() in text.lower():
                    verified = True
                    break

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"verified": verified, "doc_id": doc_id})}],
                    "isError": False
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Tool '{name}' not found."}
        }

    def _handle_resource_read(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = params.get("uri", "")
        if uri == "policy://statistics/digital_economy_2024":
            content = self.macro_df.to_json(orient="records")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [{"uri": uri, "mimeType": "application/json", "text": content}]
                }
            }
        elif uri == "policy://guidelines/ai_governance":
            file_path = UNSTRUCTURED_DATA_DIR / "ai_governance_guidelines_imda.md"
            content = file_path.read_text(encoding="utf-8")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [{"uri": uri, "mimeType": "text/markdown", "text": content}]
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": f"Resource URI '{uri}' not found."}
        }
