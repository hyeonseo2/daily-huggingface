# app/tools/mcp_client.py
import os, uuid, requests
from typing import Any, Dict, Optional

MCP_URL = os.getenv("MCP_URL", "").strip()
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

def _headers():
    h = {"Content-Type": "application/json"}
    if HF_TOKEN:
        h["Authorization"] = f"Bearer {HF_TOKEN}"
    return h

def mcp_call(method: str, params: Optional[Dict[str, Any]] = None, timeout=60):
    if not MCP_URL:
        raise RuntimeError("MCP_URL is not set")
    payload = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method, "params": params or {}}
    r = requests.post(MCP_URL, json=payload, headers=_headers(), timeout=timeout)
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise RuntimeError(j["error"])
    return j.get("result", {})

def hub_search(q: str, kind: str, limit: int = 20):
    # 툴 이름은 hf-mcp-server 관리 UI에서 실제 노출명 확인 후 필요 시 변경
    return mcp_call("tools/call", {
        "name": "hub.search",
        "arguments": {"q": q, "type": kind, "limit": limit}
    })
