import datetime

import pytest

from app.agent import DailyHuggingFaceAgent


def _iso_days_ago(days: int) -> str:
    dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


@pytest.fixture
def agent(monkeypatch):
    # Ensure MCP lookup does not interfere with tests
    monkeypatch.setattr("app.agent.mcp.hub_search", lambda **kwargs: {"items": []})
    return DailyHuggingFaceAgent(top_n=3)


def test_top_models_prefers_recent(monkeypatch, agent):
    now_items = [
        {
            "modelId": "fresh-1",
            "downloads": 1000,
            "likes": 200,
            "lastModified": _iso_days_ago(0),
        },
        {
            "modelId": "fresh-2",
            "downloads": 900,
            "likes": 150,
            "lastModified": _iso_days_ago(2),
        },
        {
            "modelId": "fresh-3",
            "downloads": 800,
            "likes": 100,
            "lastModified": _iso_days_ago(3),
        },
        {
            "modelId": "stale-1",
            "downloads": 5000,
            "likes": 500,
            "lastModified": _iso_days_ago(10),
        },
    ]

    monkeypatch.setattr(
        "app.tools.hf_api.top_models_by_downloads", lambda limit=36: now_items
    )

    results = agent.top_models()
    ids = [item["id"] for item in results]

    assert ids == ["fresh-1", "fresh-2", "fresh-3"]


def test_trending_datasets_falls_back_to_stale_only_when_needed(monkeypatch, agent):
    items = [
        {
            "id": "recent-a",
            "downloads": 2000,
            "likes": 150,
            "lastModified": _iso_days_ago(1),
        },
        {
            "id": "recent-b",
            "downloads": 1500,
            "likes": 120,
            "lastModified": _iso_days_ago(6),
        },
        {
            "id": "stale-a",
            "downloads": 9000,
            "likes": 900,
            "lastModified": _iso_days_ago(12),
        },
        {
            "id": "stale-b",
            "downloads": 8000,
            "likes": 800,
            "lastModified": _iso_days_ago(15),
        },
    ]

    def fake_trending(kind: str, limit: int = 12):
        assert kind == "dataset"
        assert limit >= 3 * 5
        return items

    monkeypatch.setattr("app.tools.hf_api.trending", fake_trending)
    monkeypatch.setattr(
        "app.tools.hf_api.top_datasets_by_downloads",
        lambda limit=36: pytest.fail("fallback should not be used when trending returns data"),
    )

    results = agent.trending_datasets()
    ids = [item["id"] for item in results]

    assert ids[:2] == ["recent-a", "recent-b"]
    # only one stale item should be used to fill the remaining slot
    assert ids[2] in {"stale-a", "stale-b"}


def test_trending_spaces_uses_stale_when_no_recent(monkeypatch, agent):
    items = [
        {
            "id": "stale-one",
            "downloads": 4000,
            "likes": 400,
            "lastModified": _iso_days_ago(20),
        },
        {
            "id": "stale-two",
            "downloads": 3500,
            "likes": 300,
            "lastModified": _iso_days_ago(30),
        },
    ]

    monkeypatch.setattr(
        "app.tools.hf_api.trending", lambda kind, limit=12: items if kind == "space" else []
    )
    monkeypatch.setattr(
        "app.tools.hf_api.top_spaces_by_likes",
        lambda limit=36: items,
    )

    results = agent.trending_spaces()
    ids = [item["id"] for item in results]

    assert ids == ["stale-one", "stale-two"]
