import datetime
from typing import Any, Optional

import pytest

from app.tools import hf_api


class DummyResponse:
    def __init__(self, payload: Any = None, error: Optional[Exception] = None):
        self._payload = payload
        self._error = error

    def raise_for_status(self):
        if self._error:
            raise self._error

    def json(self):
        return self._payload

    @property
    def text(self):
        return self._payload


def _iso_now() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def test_trending_handles_dict_payload(monkeypatch):
    captured_params = {}

    def fake_get(url, **kwargs):
        assert url.endswith("/api/trending")
        captured_params.update(kwargs.get("params", {}))
        return DummyResponse(
            payload={
                "datasets": [
                    {"id": "ds-1", "lastModifiedAt": _iso_now()},
                    {"id": "ds-2", "lastModifiedAt": _iso_now()},
                    {"id": "ds-3", "lastModified": _iso_now()},
                ],
                "models": [],
            }
        )

    monkeypatch.setattr("app.tools.hf_api.requests.get", fake_get)

    results = hf_api.trending("dataset", limit=2)

    assert [item["id"] for item in results] == ["ds-1", "ds-2"]
    assert captured_params["type"] == "dataset"
    assert captured_params["limit"] == 2
    assert all("lastModified" in item for item in results)


def _assert_camel_case(monkeypatch, func, endpoint: str):
    requested_params = []

    def fake_get(url, **kwargs):
        assert url.endswith(endpoint)
        requested_params.append(kwargs.get("params", {}))
        return DummyResponse(payload=[{"id": "ok"}])

    monkeypatch.setattr("app.tools.hf_api.requests.get", fake_get)

    result = func(limit=1)
    assert result == [{"id": "ok"}]
    assert requested_params[0]["sort"] == "lastModified"


@pytest.mark.parametrize(
    "func, endpoint",
    [
        (hf_api.recent_models, "/api/models"),
        (hf_api.recent_datasets, "/api/datasets"),
        (hf_api.recent_spaces, "/api/spaces"),
    ],
)
def test_recent_helpers_use_camel_case(monkeypatch, func, endpoint):
    _assert_camel_case(monkeypatch, func, endpoint)


def test_blog_feed_parses_latest_items(monkeypatch):
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
      <channel>
        <title>Hugging Face - Blog</title>
        <item>
          <title>Build a Domain-Specific Embedding Model in Under a Day</title>
          <pubDate>Fri, 20 Mar 2026 19:38:16 GMT</pubDate>
          <link>https://huggingface.co/blog/nvidia/domain-specific-embedding-finetune</link>
          <guid isPermaLink="false">https://huggingface.co/blog/nvidia/domain-specific-embedding-finetune</guid>
        </item>
        <item>
          <title>Another Blog</title>
          <pubDate>Fri, 20 Mar 2026 01:00:00 GMT</pubDate>
          <link>https://huggingface.co/blog/another</link>
          <guid isPermaLink="false">https://huggingface.co/blog/another</guid>
        </item>
      </channel>
    </rss>
    """

    def fake_get(url, **kwargs):
        return DummyResponse(payload=sample_xml)

    monkeypatch.setattr("app.tools.hf_api.requests.get", fake_get)
    posts = hf_api.latest_blog_posts(limit=5)

    assert len(posts) == 2
    assert posts[0]["id"] == "nvidia/domain-specific-embedding-finetune"
    assert posts[0]["title"] == "Build a Domain-Specific Embedding Model in Under a Day"
    assert posts[0]["link"] == "https://huggingface.co/blog/nvidia/domain-specific-embedding-finetune"
    assert posts[1]["id"] == "another"


def test_papers_falls_back_to_previous_day(monkeypatch):
    today = "2026-03-20"
    previous = "2026-03-19"

    calls = []

    def fake_get(url, **kwargs):
        params = kwargs.get("params", {})
        assert "date" in params
        calls.append(params["date"])

        if params["date"] == today:
            return DummyResponse(payload=[])
        if params["date"] == previous:
            return DummyResponse(
                payload=[
                    {
                        "id": "2603.19235",
                        "title": "Generation Models Know Space: Unleashing Implicit 3D Priors for Scene Understanding",
                        "summary": "scene understanding",
                        "upvotes": 63,
                        "publishedAt": "2026-03-19T17:59:58.000Z",
                        "authors": [
                            {"name": "Xianjin Wu", "hidden": False},
                            {"name": "Dingkang Liang", "hidden": False},
                        ],
                    }
                ]
            )
        raise AssertionError("unexpected date")

    monkeypatch.setattr("app.tools.hf_api.requests.get", fake_get)
    papers = hf_api.papers_for_date(date=today, limit=5)

    assert calls == [today, previous]
    assert len(papers) == 1
    assert papers[0]["id"] == "2603.19235"
    assert papers[0]["link"] == "https://huggingface.co/papers/2603.19235"
    assert papers[0]["title"].startswith("Generation Models Know Space")
    assert papers[0]["authors"] == ["Xianjin Wu", "Dingkang Liang"]
