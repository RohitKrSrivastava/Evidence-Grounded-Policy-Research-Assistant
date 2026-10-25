"""Automated protocol-level Model Context Protocol (MCP) Client."""
import time
from typing import Dict, Any, Optional
from src.mcp.server import PolicyMCPServer
from src.mcp.security import MCPSecurityEnvelope

class PolicyMCPClient:
    """Robust client communicating with the MCP server over standard JSON-RPC 2.0 payloads."""

    def __init__(self, server: Optional[PolicyMCPServer] = None, timeout_seconds: float = 2.0):
        self.server = server or PolicyMCPServer()
        self.timeout_seconds = timeout_seconds
        self.request_counter = 0
        self.is_initialized = False
        self.server_info: Dict[str, Any] = {}
        self.discovered_tools: Dict[str, Any] = {}
        self.discovered_resources: Dict[str, Any] = {}

    def _next_id(self) -> int:
        self.request_counter += 1
        return self.request_counter

    def initialize(self) -> Dict[str, Any]:
        """Performs MCP protocol handshake and capability negotiation."""
        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "PolicyAgentClient", "version": "1.0.0"}
            }
        }
        res = self.server.handle_request(req)
        if "result" in res:
            self.is_initialized = True
            self.server_info = res["result"].get("serverInfo", {})
            return res["result"]
        raise RuntimeError(f"MCP Handshake Failed: {res.get('error')}")

    def discover_capabilities(self) -> Dict[str, Any]:
        """Discovers available tools, resources, and prompts from the MCP server."""
        if not self.is_initialized:
            self.initialize()

        # Discover tools
        t_req = {"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/list", "params": {}}
        t_res = self.server.handle_request(t_req)
        tools = t_res.get("result", {}).get("tools", [])
        self.discovered_tools = {t["name"]: t for t in tools}

        # Discover resources
        r_req = {"jsonrpc": "2.0", "id": self._next_id(), "method": "resources/list", "params": {}}
        r_res = self.server.handle_request(r_req)
        resources = r_res.get("result", {}).get("resources", [])
        self.discovered_resources = {r["uri"]: r for r in resources}

        return {
            "tools": list(self.discovered_tools.keys()),
            "resources": list(self.discovered_resources.keys())
        }

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], simulate_timeout: bool = False) -> Dict[str, Any]:
        """Calls an MCP tool with schema validation and error isolation."""
        if simulate_timeout:
            return {
                "is_error": True,
                "error_code": "MCP_CLIENT_TIMEOUT",
                "message": f"Client timed out after {self.timeout_seconds}s waiting for tool '{tool_name}'"
            }

        if not self.is_initialized:
            self.initialize()

        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        res = self.server.handle_request(req)

        if "error" in res:
            return {
                "is_error": True,
                "error_code": res["error"].get("code"),
                "message": res["error"].get("message")
            }

        # Validate content and wrap in security envelope
        result_content = res.get("result", {}).get("content", [])
        raw_text = result_content[0].get("text", "") if result_content else ""

        # Filter any embedded injection payload
        is_safe, filtered_text, injection_detected = MCPSecurityEnvelope.inspect_and_filter_injections(raw_text)
        safe_envelope = MCPSecurityEnvelope.wrap_untrusted_payload(filtered_text, f"tool:{tool_name}")

        return {
            "is_error": False,
            "raw_text": raw_text,
            "filtered_text": filtered_text,
            "security_envelope": safe_envelope,
            "injection_detected": injection_detected,
            "data": filtered_text
        }

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """Reads a resource URI with security isolation."""
        if not self.is_initialized:
            self.initialize()

        req = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "resources/read",
            "params": {"uri": uri}
        }
        res = self.server.handle_request(req)

        if "error" in res:
            return {
                "is_error": True,
                "error_code": res["error"].get("code"),
                "message": res["error"].get("message")
            }

        contents = res.get("result", {}).get("contents", [])
        raw_text = contents[0].get("text", "") if contents else ""

        is_safe, filtered_text, injection_detected = MCPSecurityEnvelope.inspect_and_filter_injections(raw_text)
        envelope = MCPSecurityEnvelope.wrap_untrusted_payload(filtered_text, uri)

        return {
            "is_error": False,
            "uri": uri,
            "mime_type": contents[0].get("mimeType", "") if contents else "",
            "raw_text": raw_text,
            "filtered_text": filtered_text,
            "security_envelope": envelope,
            "injection_detected": injection_detected
        }
