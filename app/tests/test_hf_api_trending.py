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
