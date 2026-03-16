import os
import re
import requests
import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlparse

MCP_URL = os.getenv("MCP_URL", "").strip()
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

_MCP_SESSION_ID: Optional[str] = None


def _headers():
    h = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if HF_TOKEN:
        h["Authorization"] = f"Bearer {HF_TOKEN}"
    return h


def _request(method: str, params: Optional[Dict[str, Any]] = None, timeout=60, use_session=True):
    if not MCP_URL:
        raise RuntimeError("MCP_URL is not set")

    headers = _headers()
    if use_session and _MCP_SESSION_ID:
        headers["mcp-session-id"] = _MCP_SESSION_ID

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    }

    r = requests.post(MCP_URL, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r


def _ensure_session():
    global _MCP_SESSION_ID
    if _MCP_SESSION_ID:
        return

    r = _request(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "daily-huggingface", "version": "1.0"},
            "capabilities": {},
        },
        use_session=False,
    )

    sid = r.headers.get("mcp-session-id")
    if sid:
        _MCP_SESSION_ID = sid


def _parse_k_abbrev(value: str) -> Optional[float]:
    try:
        v = value.strip().replace(",", "").upper()
        if v.endswith("K"):
            return float(v[:-1]) * 1_000
        if v.endswith("M"):
            return float(v[:-1]) * 1_000_000
        if v.endswith("B"):
            return float(v[:-1]) * 1_000_000_000
        return float(v)
    except Exception:
        return None


def _extract_items_from_text(text: str):
    items = []

    if not text or "No repositories found" in text:
        return items

    section_re = re.compile(r"^###\s*(?P<name>[^\n]+)\n(?P<body>.*?)(?=^###\s|\Z)", re.M | re.S)

    for m in section_re.finditer(text):
        rid = (m.group("name") or "").strip()
        body = m.group("body") or ""

        # markdown output can include hf.co or huggingface.co links
        link_match = re.search(
            r"\*\*Link:\*\*\s*\[(https?://(?:hf|huggingface)\.co/[^\]]+)\]\((https?://(?:hf|huggingface)\.co/[^)]+)\)",
            body,
        )

        link = link_match.group(2) if link_match else f"https://huggingface.co/{rid}"

        if link.startswith("https://") or link.startswith("http://"):
            parsed = urlparse(link)
            parsed_slug = parsed.path.lstrip("/")
            if parsed_slug:
                rid = parsed_slug

        m_dl = re.search(r"\*\*Downloads:\*\*\s*([0-9,.kKmMbB]+)", body)
        m_lk = re.search(r"\*\*Likes:\*\*\s*([0-9,.kKmMbB]+)", body)
        downloads = _parse_k_abbrev(m_dl.group(1)) if m_dl else None
        likes = _parse_k_abbrev(m_lk.group(1)) if m_lk else None

        items.append(
            {
                "id": rid,
                "link": link,
                "downloads": downloads,
                "likes": likes,
            }
        )

    return items


def _normalize_result(result: Dict[str, Any]):
    if isinstance(result, dict) and "items" in result:
        return result.get("items") or []

    if isinstance(result, dict) and isinstance(result.get("content"), list):
        texts = []
        for chunk in result.get("content", []):
            if isinstance(chunk, dict) and isinstance(chunk.get("text"), str):
                texts.append(chunk["text"])
        return _extract_items_from_text("\n".join(texts))

    return []


def mcp_call(method: str, params: Optional[Dict[str, Any]] = None, timeout=60):
    try:
        _ensure_session()
    except Exception:
        pass

    r = _request(method, params=params or {}, timeout=timeout, use_session=True)
    j = r.json()

    if "error" in j:
        if _MCP_SESSION_ID and "Session ID required" in str(j.get("error")):
            _ensure_session()
            r = _request(method, params=params or {}, timeout=timeout, use_session=True)
            j = r.json()
        if "error" in j:
            raise RuntimeError(j["error"])

    return _normalize_result(j.get("result", {}))


def hub_search(q: str, kind: str, limit: int = 20):
    # hf-mcp docs: this search endpoint is exposed as hub_repo_search
    query = "" if q in ("*", None, "") else q
    return mcp_call(
        "tools/call",
        {
            "name": "hub_repo_search",
            "arguments": {
                "query": query,
                "repo_types": [kind],
                "sort": "trendingScore",
                "limit": limit,
            },
        },
    )
