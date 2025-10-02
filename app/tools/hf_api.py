# app/tools/hf_api.py
import logging
import os
import requests
from typing import List, Dict, Any

BASE = "https://huggingface.co"
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

logger = logging.getLogger(__name__)

def _headers():
    return {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

def _extract_trending_items(data: Any, kind: str) -> List[Dict[str, Any]]:
    """Normalize the payload returned by /api/trending."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if not isinstance(data, dict):
        return []

    # Typical payload shape: {"models": [...], "datasets": [...], "spaces": [...]}.
    plural_key = f"{kind}s"
    candidates = [plural_key, kind, "items"]
    for key in candidates:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            items = value.get("items")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def trending(kind: str, limit: int = 12) -> List[Dict[str, Any]]:
    """
    트렌딩 API: 401/403 등 에러나면 빈 리스트 반환(상위 레이어에서 폴백).
    kind in {"model","dataset","space"}
    """
    try:
        params = {"type": kind}
        # 일부 배포에서는 limit 파라미터가 없지만, 지원 시 활용한다.
        params["limit"] = limit
        r = requests.get(
            f"{BASE}/api/trending",
            params=params,
            headers=_headers(),
            timeout=30,
        )
        r.raise_for_status()
        raw_items = _extract_trending_items(r.json(), kind)
        for item in raw_items:
            # ensure timestamp fields propagate downstream
            if "lastModified" not in item and "lastModifiedAt" in item:
                item["lastModified"] = item.get("lastModifiedAt")
        return raw_items[:limit]
    except requests.HTTPError as err:
        logger.warning("hf_api.trending(%s) failed: %s", kind, err)
        return []
    except requests.RequestException as err:
        logger.warning("hf_api.trending(%s) request failed: %s", kind, err)
        return []
    except Exception as err:
        logger.warning("hf_api.trending(%s) unexpected error: %s", kind, err)
        return []

def top_models_by_downloads(limit: int = 12) -> List[Dict[str, Any]]:
    try:
        r = requests.get(
            f"{BASE}/api/models",
            params={"limit": limit, "sort": "downloads"},
            headers=_headers(),
            timeout=45,
        )
        r.raise_for_status()
        return r.json() or []
    except requests.HTTPError as err:
        logger.warning("hf_api.top_models_by_downloads failed: %s", err)
        return []
    except requests.RequestException as err:
        logger.warning("hf_api.top_models_by_downloads request failed: %s", err)
        return []

def recent_models(limit: int = 12) -> List[Dict[str, Any]]:
    try:
        r = requests.get(
            f"{BASE}/api/models",
            params={"limit": limit, "sort": "lastModified", "full": "1"},
            headers=_headers(),
            timeout=45,
        )
        r.raise_for_status()
        return r.json() or []
    except requests.HTTPError as err:
        logger.warning("hf_api.recent_models failed: %s", err)
        return []
    except requests.RequestException as err:
        logger.warning("hf_api.recent_models request failed: %s", err)
        return []

def top_datasets_by_downloads(limit: int = 12) -> List[Dict[str, Any]]:
    try:
        r = requests.get(
            f"{BASE}/api/datasets",
            params={"limit": limit, "sort": "downloads"},
            headers=_headers(),
            timeout=45,
        )
        r.raise_for_status()
        return r.json() or []
    except requests.HTTPError as err:
        logger.warning("hf_api.top_datasets_by_downloads failed: %s", err)
        return []
    except requests.RequestException as err:
        logger.warning("hf_api.top_datasets_by_downloads request failed: %s", err)
        return []

def recent_datasets(limit: int = 12) -> List[Dict[str, Any]]:
    try:
        r = requests.get(
            f"{BASE}/api/datasets",
            params={"limit": limit, "sort": "lastModified", "full": "1"},
            headers=_headers(),
            timeout=45,
        )
        r.raise_for_status()
        return r.json() or []
    except requests.HTTPError as err:
        logger.warning("hf_api.recent_datasets failed: %s", err)
        return []
    except requests.RequestException as err:
        logger.warning("hf_api.recent_datasets request failed: %s", err)
        return []

def top_spaces_by_likes(limit: int = 12) -> List[Dict[str, Any]]:
    try:
        r = requests.get(
            f"{BASE}/api/spaces",
            params={"limit": limit, "sort": "likes"},
            headers=_headers(),
            timeout=45,
        )
        r.raise_for_status()
        return r.json() or []
    except requests.HTTPError as err:
        logger.warning("hf_api.top_spaces_by_likes failed: %s", err)
        return []
    except requests.RequestException as err:
        logger.warning("hf_api.top_spaces_by_likes request failed: %s", err)
        return []

def recent_spaces(limit: int = 12) -> List[Dict[str, Any]]:
    try:
        r = requests.get(
            f"{BASE}/api/spaces",
            params={"limit": limit, "sort": "lastModified", "full": "1"},
            headers=_headers(),
            timeout=45,
        )
        r.raise_for_status()
        return r.json() or []
    except requests.HTTPError as err:
        logger.warning("hf_api.recent_spaces failed: %s", err)
        return []
    except requests.RequestException as err:
        logger.warning("hf_api.recent_spaces request failed: %s", err)
        return []

def normalize_items(raw, id_key="id"):
    out=[]
    for it in raw or []:
        rid = it.get(id_key) or it.get("modelId") or it.get("id")
        if not rid:
            continue
        link = f"{BASE}/{rid}"
        last_modified = (
            it.get("lastModified")
            or it.get("lastModifiedAt")
            or it.get("updatedAt")
            or it.get("modifiedAt")
            or it.get("createdAt")
        )
        updated_at = (
            it.get("updatedAt")
            or it.get("lastModified")
            or it.get("lastModifiedAt")
            or it.get("modifiedAt")
            or it.get("createdAt")
        )
        out.append({
            "id": rid,
            "link": link,
            "likes": it.get("likes"),
            "downloads": it.get("downloads"),
            "library": it.get("library_name") or it.get("library"),
            "updatedAt": updated_at,
            "createdAt": it.get("createdAt"),
            "lastModified": last_modified,
        })
    return out
