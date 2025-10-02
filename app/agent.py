# app/agent.py
import os, math, json, datetime
from typing import List, Dict, Any, Optional, Iterable, Tuple, Sequence

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

    @staticmethod
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

    def _split_recent_stale(
        self, items: Iterable[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
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
            dt = self._parse_ts(ts)
            if dt and (now - dt).days <= 7:
                recent.append(item)
            else:
                stale.append(item)

        return recent, stale

    def _filter_recent(self, items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return the top-N items prioritising entries updated within seven days."""

        recent, stale = self._split_recent_stale(items)

        def _sort(items_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            return sorted(items_list, key=_score, reverse=True)

        ordered: List[Dict[str, Any]] = []
        ordered.extend(_sort(recent)[: self.top_n])
        if len(ordered) < self.top_n:
            needed = self.top_n - len(ordered)
            ordered.extend(_sort(stale)[:needed])
        return ordered

    def _merge_unique(
        self, primary: Iterable[Dict[str, Any]], secondary: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        seen = {item["id"] for item in primary}
        merged = list(primary)
        for item in secondary or []:
            item_id = item.get("id")
            if not item_id or item_id in seen:
                continue
            merged.append(item)
            seen.add(item_id)
        return merged

    def _collect_from_mcp(
        self, kind: str, id_fields: Sequence[str]
    ) -> List[Dict[str, Any]]:
        try:
            res = mcp.hub_search(q="*", kind=kind, limit=self.top_n * 5)
        except Exception:
            return []

        items = res.get("items", []) or []
        normalized: List[Dict[str, Any]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            rid = None
            for field in id_fields:
                candidate = it.get(field)
                if candidate:
                    rid = candidate
                    break
            if not rid:
                continue
            last_modified = (
                it.get("lastModified")
                or it.get("lastModifiedAt")
                or it.get("updatedAt")
                or it.get("modifiedAt")
            )
            updated_at = (
                it.get("updatedAt")
                or it.get("lastModified")
                or it.get("lastModifiedAt")
                or it.get("modifiedAt")
            )
            normalized.append(
                {
                    "id": rid,
                    "link": f"https://huggingface.co/{rid}",
                    "downloads": it.get("downloads"),
                    "likes": it.get("likes"),
                    "library": it.get("library_name") or it.get("library"),
                    "updatedAt": updated_at,
                    "createdAt": it.get("createdAt"),
                    "lastModified": last_modified,
                }
            )
        return normalized

    # ---- 수집 ----
    def top_models(self) -> List[Dict[str, Any]]:
        # 1) MCP 시도
        combined = self._collect_from_mcp("model", ["id", "modelId"])
        if combined:
            filtered = self._filter_recent(combined)
            if len(filtered) >= self.top_n:
                return filtered[: self.top_n]

        # 2) 폴백: REST - 최근 정렬 우선
        recent_raw = hf_api.recent_models(limit=self.top_n * 5)
        recent_norm = hf_api.normalize_items(recent_raw, id_key="modelId")
        combined = self._merge_unique(combined, recent_norm) if combined else recent_norm
        recent_bucket, _ = self._split_recent_stale(combined)
        if len(combined) < self.top_n or not recent_bucket:
            downloads_raw = hf_api.top_models_by_downloads(limit=self.top_n * 5)
            downloads_norm = hf_api.normalize_items(downloads_raw, id_key="modelId")
            combined = self._merge_unique(combined, downloads_norm)
        filtered = self._filter_recent(combined)
        return filtered[: self.top_n]

    def trending_datasets(self) -> List[Dict[str, Any]]:
        combined = self._collect_from_mcp("dataset", ["id", "datasetId"])
        if combined:
            filtered = self._filter_recent(combined)
            if len(filtered) >= self.top_n:
                return filtered[: self.top_n]

        # 1) 트렌딩 시도
        raw = hf_api.trending("dataset", limit=self.top_n * 5)
        if raw:
            trending_norm = hf_api.normalize_items(raw, id_key="id")
            combined = self._merge_unique(combined, trending_norm) if combined else trending_norm

        recent_bucket, _ = self._split_recent_stale(combined)
        if len(combined) < self.top_n or not recent_bucket:
            recent_raw = hf_api.recent_datasets(limit=self.top_n * 5)
            recent_norm = hf_api.normalize_items(recent_raw, id_key="id")
            combined = self._merge_unique(combined, recent_norm)

        recent_bucket, _ = self._split_recent_stale(combined)
        if len(combined) < self.top_n or not recent_bucket:
            alt = hf_api.top_datasets_by_downloads(limit=self.top_n * 5)
            norm_alt = hf_api.normalize_items(alt, id_key="id")
            combined = self._merge_unique(combined, norm_alt)

        return self._filter_recent(combined)[: self.top_n]

    def trending_spaces(self) -> List[Dict[str, Any]]:
        combined = self._collect_from_mcp("space", ["id", "spaceId"])
        if combined:
            filtered = self._filter_recent(combined)
            if len(filtered) >= self.top_n:
                return filtered[: self.top_n]

        # 1) 트렌딩 시도
        raw = hf_api.trending("space", limit=self.top_n * 5)
        if raw:
            trending_norm = hf_api.normalize_items(raw, id_key="id")
            combined = self._merge_unique(combined, trending_norm) if combined else trending_norm

        recent_bucket, _ = self._split_recent_stale(combined)
        if len(combined) < self.top_n or not recent_bucket:
            recent_raw = hf_api.recent_spaces(limit=self.top_n * 5)
            recent_norm = hf_api.normalize_items(recent_raw, id_key="id")
            combined = self._merge_unique(combined, recent_norm)

        recent_bucket, _ = self._split_recent_stale(combined)
        if len(combined) < self.top_n or not recent_bucket:
            alt = hf_api.top_spaces_by_likes(limit=self.top_n * 5)
            norm_alt = hf_api.normalize_items(alt, id_key="id")
            combined = self._merge_unique(combined, norm_alt)

        return self._filter_recent(combined)[: self.top_n]


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
