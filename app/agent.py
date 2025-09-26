# app/agent.py
import os, math, json, datetime
from typing import List, Dict, Any, Optional

from .tools import hf_api
from .tools import mcp_client as mcp

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

def _score(item: Dict[str, Any]) -> float:
    """간단 점수: log(downloads)*0.6 + log(likes)*0.3 + recency*0.1"""
    def _safe_num(x):
        return x if isinstance(x, (int, float)) and x >= 0 else 0
    d = math.log10(_safe_num(item.get("downloads")) + 1)
    l = math.log10(_safe_num(item.get("likes")) + 1)
    rec = 0.0
    ts = item.get("updatedAt")
    if ts:
        try:
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            days = (datetime.datetime.utcnow().replace(tzinfo=dt.tzinfo) - dt).days
            rec = max(0.0, 1.0 - min(days, 30) / 30.0)
        except:
            pass
    return 0.6 * d + 0.3 * l + 0.1 * rec

class DailyHuggingFaceAgent:
    def __init__(self, top_n: int = 12):
        self.top_n = top_n

    # ---- 수집 ----
    def top_models(self) -> List[Dict[str, Any]]:
        # 1) MCP 시도
        try:
            res = mcp.hub_search(q="*", kind="model", limit=self.top_n * 3)
            items = res.get("items", [])
            norm=[]
            for it in items:
                rid = it.get("id") or it.get("modelId")
                if not rid: continue
                norm.append({
                    "id": rid,
                    "link": f"https://huggingface.co/{rid}",
                    "downloads": it.get("downloads"),
                    "likes": it.get("likes"),
                    "library": it.get("library_name"),
                    "updatedAt": it.get("lastModified")
                })
            if norm:
                norm.sort(key=_score, reverse=True)
                return norm[:self.top_n]
        except Exception:
            pass
        # 2) 폴백: REST
        raw = hf_api.top_models_by_downloads(top=self.top_n)
        return hf_api.normalize_items(raw, id_key="modelId")

    def trending_datasets(self) -> List[Dict[str, Any]]:
        # 1) 트렌딩 시도
        raw = hf_api.trending("dataset", top=self.top_n)
        if raw:
            return hf_api.normalize_items(raw, id_key="id")
        # 2) 폴백: 다운로드 정렬
        alt = hf_api.top_datasets_by_downloads(top=self.top_n)
        return hf_api.normalize_items(alt, id_key="id")

    def trending_spaces(self) -> List[Dict[str, Any]]:
        # 1) 트렌딩 시도
        raw = hf_api.trending("space", top=self.top_n)
        if raw:
            return hf_api.normalize_items(raw, id_key="id")
        # 2) 폴백: 좋아요 정렬
        alt = hf_api.top_spaces_by_likes(top=self.top_n)
        return hf_api.normalize_items(alt, id_key="id")


    # ---- 요약(옵션) ----
    def summarize_items(self, section_name: str, items: List[Dict[str, Any]]) -> Optional[str]:
        if not OPENAI_API_KEY or not items:
            return None
        try:
            prompt = {
                "role": "user",
                "content": (
                    f"Summarize the following Hugging Face {section_name} list into 2-3 concise sentences in Korean. "
                    f"Focus on common themes and notable trends. Items JSON:\n{json.dumps(items, ensure_ascii=False)[:8000]}"
                ),
            }
            import requests
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "system", "content": "You are a helpful assistant."}, prompt],
                    "temperature": 0.3,
                },
                timeout=60,
            )
            r.raise_for_status()
            j = r.json()
            return j["choices"][0]["message"]["content"].strip()
        except Exception:
            return None
