import datetime
from typing import Optional

import pytest
import requests

from app.agent import DailyHuggingFaceAgent


class DummyResponse:
    def __init__(self, payload=None, error: Optional[Exception] = None):
        self._payload = payload
        self._error = error

    def raise_for_status(self):
        if self._error:
            raise self._error

    def json(self):
        return self._payload


def _iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@pytest.fixture
def agent(monkeypatch):
    monkeypatch.setattr("app.agent.mcp.hub_search", lambda **kwargs: {"items": []})
    return DailyHuggingFaceAgent(top_n=2)


def test_top_models_recovers_when_recent_models_http_error(monkeypatch, agent):
    def fake_get(url, **kwargs):
        params = kwargs.get("params", {})
        if url.endswith("/api/models") and params.get("sort") == "lastModified":
            return DummyResponse(error=requests.HTTPError("recent models boom"))
        if url.endswith("/api/models") and params.get("sort") == "downloads":
            return DummyResponse(
                payload=[
                    {
                        "modelId": "download-fallback",
                        "downloads": 123,
                        "likes": 45,
                        "lastModified": _iso_now(),
                    }
                ]
            )
        raise AssertionError("unexpected request: %s %s" % (url, params))

    monkeypatch.setattr("app.tools.hf_api.requests.get", fake_get)

    results = agent.top_models()

    assert [item["id"] for item in results] == ["download-fallback"]


def test_trending_datasets_recovers_when_recent_http_error(monkeypatch, agent):
    monkeypatch.setattr("app.tools.hf_api.trending", lambda kind, limit=12: [])

    def fake_get(url, **kwargs):
        params = kwargs.get("params", {})
        if url.endswith("/api/datasets") and params.get("sort") == "lastModified":
            return DummyResponse(error=requests.HTTPError("recent datasets boom"))
        if url.endswith("/api/datasets") and params.get("sort") == "downloads":
            return DummyResponse(
                payload=[
                    {
                        "id": "dataset-fallback",
                        "downloads": 999,
                        "likes": 88,
                        "lastModified": _iso_now(),
                    }
                ]
            )
        raise AssertionError("unexpected request: %s %s" % (url, params))

    monkeypatch.setattr("app.tools.hf_api.requests.get", fake_get)

    results = agent.trending_datasets()

    assert [item["id"] for item in results] == ["dataset-fallback"]


def test_trending_spaces_recovers_when_recent_http_error(monkeypatch, agent):
    monkeypatch.setattr("app.tools.hf_api.trending", lambda kind, limit=12: [])

    def fake_get(url, **kwargs):
        params = kwargs.get("params", {})
        if url.endswith("/api/spaces") and params.get("sort") == "lastModified":
            return DummyResponse(error=requests.HTTPError("recent spaces boom"))
        if url.endswith("/api/spaces") and params.get("sort") == "likes":
            return DummyResponse(
                payload=[
                    {
                        "id": "space-fallback",
                        "downloads": 10,
                        "likes": 500,
                        "lastModified": _iso_now(),
                    }
                ]
            )
        raise AssertionError("unexpected request: %s %s" % (url, params))

    monkeypatch.setattr("app.tools.hf_api.requests.get", fake_get)

    results = agent.trending_spaces()

    assert [item["id"] for item in results] == ["space-fallback"]
