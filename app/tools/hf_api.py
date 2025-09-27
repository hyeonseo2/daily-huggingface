# app/tools/hf_api.py
import os
import requests
from typing import List, Dict, Any

BASE = "https://huggingface.co"
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

def _headers():
    return {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

def trending(kind: str, limit: int = 12) -> List[Dict[str, Any]]:
    """
    트렌딩 API: 401/403 등 에러나면 빈 리스트 반환(상위 레이어에서 폴백).
    kind in {"model","dataset","space"}
    """
    try:
        r = requests.get(f"{BASE}/api/trending",
                         params={"type": kind},
                         headers=_headers(), timeout=30)
        r.raise_for_status()
        data = r.json() or []
        for item in data:
            # ensure timestamp fields propagate downstream
            if "lastModified" not in item and "lastModifiedAt" in item:
                item["lastModified"] = item.get("lastModifiedAt")
        return data[:limit]
    except requests.HTTPError:
        return []
    except Exception:
        return []

def top_models_by_downloads(limit: int = 12) -> List[Dict[str, Any]]:
    r = requests.get(f"{BASE}/api/models",
                     params={"limit": limit, "sort": "downloads"},
                     headers=_headers(), timeout=45)
    r.raise_for_status()
    return r.json() or []

def top_datasets_by_downloads(limit: int = 12) -> List[Dict[str, Any]]:
    r = requests.get(f"{BASE}/api/datasets",
                     params={"limit": limit, "sort": "downloads"},
                     headers=_headers(), timeout=45)
    r.raise_for_status()
    return r.json() or []

def top_spaces_by_likes(limit: int = 12) -> List[Dict[str, Any]]:
    r = requests.get(f"{BASE}/api/spaces",
                     params={"limit": limit, "sort": "likes"},
                     headers=_headers(), timeout=45)
    r.raise_for_status()
    return r.json() or []

def normalize_items(raw, id_key="id"):
    out=[]
    for it in raw or []:
        rid = it.get(id_key) or it.get("modelId") or it.get("id")
        if not rid:
            continue
        link = f"{BASE}/{rid}"
        out.append({
            "id": rid,
            "link": link,
            "likes": it.get("likes"),
            "downloads": it.get("downloads"),
            "library": it.get("library_name") or it.get("library"),
            "updatedAt": it.get("lastModified") or it.get("lastModifiedAt") or it.get("updatedAt"),
            "createdAt": it.get("createdAt"),
            "lastModified": it.get("lastModified") or it.get("updatedAt"),
        })
    return out
