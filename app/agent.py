# app/agent.py
import os, math, json, datetime
from typing import List, Dict, Any, Optional, Iterable

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
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            days = (now - dt.astimezone(datetime.timezone.utc)).days
            rec = max(0.0, 1.0 - min(days, 30) / 30.0)
        except:
            pass
    return 0.6 * d + 0.3 * l + 0.1 * rec

class DailyHuggingFaceAgent:
    def __init__(self, top_n: int = 12):
        self.top_n = top_n

    def _filter_recent(self, items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return the top-N items prioritising entries updated within seven days."""

        def _parse_ts(value: Optional[str]) -> Optional[datetime.datetime]:
            if not value:
                return None
            try:
                if value.endswith("Z"):
                    value = value.replace("Z", "+00:00")
                dt = datetime.datetime.fromisoformat(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                return dt.astimezone(datetime.timezone.utc)
            except Exception:
                return None

        now = datetime.datetime.now(datetime.timezone.utc)
        recent: List[Dict[str, Any]] = []
        stale: List[Dict[str, Any]] = []

        for item in items or []:
            ts = (
                item.get("updatedAt")
                or item.get("lastModified")
                or item.get("lastModifiedAt")
                or item.get("createdAt")
            )
            dt = _parse_ts(ts)
            if dt and (now - dt).days <= 7:
                recent.append(item)
            else:
                stale.append(item)

        def _sort(items_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return sorted(items_list, key=_score, reverse=True)

        ordered: List[Dict[str, Any]] = []
        ordered.extend(_sort(recent)[: self.top_n])
        if len(ordered) < self.top_n:
            needed = self.top_n - len(ordered)
            ordered.extend(_sort(stale)[:needed])
        return ordered

    # ---- 수집 ----
    def top_models(self) -> List[Dict[str, Any]]:
        # 1) MCP 시도
        try:
            res = mcp.hub_search(q="*", kind="model", limit=self.top_n * 5)
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
                    "updatedAt": it.get("lastModified") or it.get("updatedAt"),
                    "createdAt": it.get("createdAt"),
                })
            if norm:
                filtered = self._filter_recent(norm)
                if filtered:
                    return filtered[: self.top_n]
        except Exception:
            pass
        # 2) 폴백: REST
        raw = hf_api.top_models_by_downloads(limit=self.top_n * 5)
        norm = hf_api.normalize_items(raw, id_key="modelId")
        filtered = self._filter_recent(norm)
        return filtered[: self.top_n]

    def trending_datasets(self) -> List[Dict[str, Any]]:
        # 1) 트렌딩 시도
        raw = hf_api.trending("dataset", limit=self.top_n * 5)
        if raw:
            norm = hf_api.normalize_items(raw, id_key="id")
            filtered = self._filter_recent(norm)
            if filtered:
                return filtered[: self.top_n]
        # 2) 폴백: 다운로드 정렬
        alt = hf_api.top_datasets_by_downloads(limit=self.top_n * 5)
        norm_alt = hf_api.normalize_items(alt, id_key="id")
        return self._filter_recent(norm_alt)[: self.top_n]

    def trending_spaces(self) -> List[Dict[str, Any]]:
        # 1) 트렌딩 시도
        raw = hf_api.trending("space", limit=self.top_n * 5)
        if raw:
            norm = hf_api.normalize_items(raw, id_key="id")
            filtered = self._filter_recent(norm)
            if filtered:
                return filtered[: self.top_n]
        # 2) 폴백: 좋아요 정렬
        alt = hf_api.top_spaces_by_likes(limit=self.top_n * 5)
        norm_alt = hf_api.normalize_items(alt, id_key="id")
        return self._filter_recent(norm_alt)[: self.top_n]


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
