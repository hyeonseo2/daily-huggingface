import datetime
import logging
import os
import re
from email.utils import parsedate_to_datetime
import requests
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree as ET

BASE = "https://huggingface.co"
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

BLOG_FEED_URL = "https://huggingface.co/blog/feed.xml"
BLOG_API_URL = "https://huggingface.co/api/blog"
PAPERS_API_URL = "https://huggingface.co/api/papers"

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


def _to_iso(dt: datetime.datetime) -> str:
    return dt.astimezone(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_xml_text(tag: Any) -> str:
    if tag is None:
        return ""
    return re.sub(r"\s+", " ", (tag.text or "")).strip()


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


def _normalize_papers_raw(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for it in raw or []:
        if not isinstance(it, dict):
            continue
        pid = it.get("id")
        if not pid:
            continue

        published = it.get("publishedAt")
        try:
            if published and isinstance(published, str):
                dt = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
            else:
                dt = None
        except Exception:
            dt = None

        authors = [a.get("name") for a in it.get("authors", []) if isinstance(a, dict) and a.get("name")]

        out.append(
            {
                "id": pid,
                "title": it.get("title") or pid,
                "link": f"{BASE}/papers/{pid}",
                "summary": it.get("summary"),
                "upvotes": it.get("upvotes"),
                "publishedAt": published,
                "updatedAt": published,
                "createdAt": published,
                "authors": authors,
                "raw_published": dt,
            }
        )

    out.sort(
        key=lambda x: (
            x.get("upvotes") if isinstance(x.get("upvotes"), (int, float)) else -1,
            x.get("raw_published") or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc),
        ),
        reverse=True,
    )
    return out


def papers_for_date(date: Optional[str] = None, limit: int = 12) -> List[Dict[str, Any]]:
    """Fetch papers for the given date. If date has no result, try previous day once."""
    today = datetime.datetime.now(datetime.timezone.utc).date()
    start = today
    if date:
        try:
            start = datetime.date.fromisoformat(date)
        except Exception:
            start = datetime.datetime.now(datetime.timezone.utc).date()

    candidates = [start, start - datetime.timedelta(days=1)]

    last_err = None
    for d in candidates:
        try:
            r = requests.get(
                PAPERS_API_URL,
                params={"date": d.isoformat()},
                headers=_headers(),
                timeout=30,
            )
            r.raise_for_status()
            data = r.json() or []
            normalized = _normalize_papers_raw(data)
            if normalized:
                return normalized[:limit]
        except requests.HTTPError as err:
            last_err = err
            logger.warning("hf_api.papers_for_date(%s) failed: %s", d.isoformat(), err)
            continue
        except requests.RequestException as err:
            last_err = err
            logger.warning("hf_api.papers_for_date(%s) request failed: %s", d.isoformat(), err)
            continue
        except Exception as err:
            last_err = err
            logger.warning("hf_api.papers_for_date(%s) unexpected error: %s", d.isoformat(), err)
            continue

    if last_err:
        logger.warning("hf_api.papers_for_date all fallback attempts failed: %s", last_err)
    return []


def latest_blog_posts(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch latest blog posts from HF API with RSS fallback."""
    # Preferred: API (richer metadata including upvotes).
    try:
        r = requests.get(BLOG_API_URL, headers=_headers(), timeout=30)
        r.raise_for_status()
        payload = r.json() or {}
        raw = payload.get("allBlogs") if isinstance(payload, dict) else None
        items = []
        if isinstance(raw, list):
            for entry in raw[:limit]:
                if not isinstance(entry, dict):
                    continue
                slug = entry.get("slug")
                url = entry.get("url")
                if not url or not slug:
                    continue

                link = url if url.startswith("http") else f"{BASE}{url}"
                pub = entry.get("publishedAt")
                pub_iso = None
                try:
                    if pub:
                        dt = datetime.datetime.fromisoformat(pub.replace("Z", "+00:00"))
                        pub_iso = _to_iso(dt)
                except Exception:
                    pub_iso = None

                authors = [a.get("name") for a in entry.get("authorsData", []) if isinstance(a, dict) and a.get("name")]

                items.append(
                    {
                        "id": slug,
                        "title": entry.get("title") or slug,
                        "link": link,
                        "upvotes": entry.get("upvotes"),
                        "publishedAt": pub_iso,
                        "updatedAt": pub_iso,
                        "createdAt": pub_iso,
                        "raw_published": dt if "dt" in locals() else None,
                        "authors": authors,
                    }
                )

                if len(items) >= limit:
                    break

        items.sort(key=lambda x: x.get("raw_published") or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
        items = items[:limit]
        if items:
            return items
    except requests.HTTPError as err:
        logger.warning("hf_api.latest_blog_posts api call failed: %s", err)
    except requests.RequestException as err:
        logger.warning("hf_api.latest_blog_posts api request failed: %s", err)
    except Exception as err:
        logger.warning("hf_api.latest_blog_posts api unexpected error: %s", err)

    # Fallback: RSS feed (lightweight)
    try:
        r = requests.get(BLOG_FEED_URL, headers=_headers(), timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        channel = root.find("channel")
        if channel is None:
            return []

        items = []
        for item in list(channel.findall("item"))[:limit]:
            title = _parse_xml_text(item.find("title"))
            link = _parse_xml_text(item.find("link"))
            if not link:
                continue
            pid = link.split("/blog/")[-1] if "/blog/" in link else link

            pub_raw = _parse_xml_text(item.find("pubDate"))
            pub_iso = None
            dt_local = None
            try:
                if pub_raw:
                    dt_local = parsedate_to_datetime(pub_raw)
                    if dt_local:
                        pub_iso = _to_iso(dt_local)
            except Exception:
                pub_iso = None

            items.append(
                {
                    "id": pid,
                    "title": title or pid,
                    "link": link,
                    "publishedAt": pub_iso,
                    "updatedAt": pub_iso,
                    "createdAt": pub_iso,
                    "raw_published": dt_local,
                }
            )

            if len(items) >= limit:
                break

        items.sort(key=lambda x: x.get("raw_published") or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
        return items[:limit]

    except requests.HTTPError as err:
        logger.warning("hf_api.latest_blog_posts rss failed: %s", err)
        return []
    except requests.RequestException as err:
        logger.warning("hf_api.latest_blog_posts rss request failed: %s", err)
        return []
    except ET.ParseError as err:
        logger.warning("hf_api.latest_blog_posts parse error: %s", err)
        return []
    except Exception as err:
        logger.warning("hf_api.latest_blog_posts unexpected error: %s", err)
        return []


def normalize_items(raw, id_key="id"):
    out = []
    for it in raw or []:
        if not isinstance(it, dict):
            continue
        rid = it.get(id_key) or it.get("modelId") or it.get("id")
        if not rid:
            continue
        link = it.get("link") or f"{BASE}/{rid}"
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
            "upvotes": it.get("upvotes"),
            "downloads": it.get("downloads"),
            "library": it.get("library_name") or it.get("library"),
            "updatedAt": updated_at,
            "createdAt": it.get("createdAt"),
            "lastModified": last_modified,
            "title": it.get("title") or it.get("name") or it.get("label"),
            "authors": it.get("authors") or [],
            "summary": it.get("summary"),
        })
    return out
