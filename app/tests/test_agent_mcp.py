import datetime

from app.agent import DailyHuggingFaceAgent


def _iso_now() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def test_trending_datasets_prefers_mcp(monkeypatch):
    agent = DailyHuggingFaceAgent(top_n=1)

    def fake_hub_search(**kwargs):
        assert kwargs["kind"] == "dataset"
        return {
            "items": [
                {
                    "id": "dataset-from-mcp",
                    "lastModified": _iso_now(),
                    "likes": 10,
                    "downloads": 20,
                }
            ]
        }

    monkeypatch.setattr("app.agent.mcp.hub_search", fake_hub_search)
    monkeypatch.setattr("app.tools.hf_api.trending", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not call REST trending")))

    results = agent.trending_datasets()
    assert [item["id"] for item in results] == ["dataset-from-mcp"]


def test_trending_spaces_prefers_mcp(monkeypatch):
    agent = DailyHuggingFaceAgent(top_n=1)

    def fake_hub_search(**kwargs):
        assert kwargs["kind"] == "space"
        return {
            "items": [
                {
                    "id": "space-from-mcp",
                    "lastModified": _iso_now(),
                    "likes": 5,
                    "downloads": 3,
                }
            ]
        }

    monkeypatch.setattr("app.agent.mcp.hub_search", fake_hub_search)
    monkeypatch.setattr("app.tools.hf_api.trending", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not call REST trending")))

    results = agent.trending_spaces()
    assert [item["id"] for item in results] == ["space-from-mcp"]
