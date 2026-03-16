"""Minimal end-to-end test for newsletter generation flow.

This test documents the integration intent: keep one stable scenario that verifies
`main.main()` wires the agent outputs into `render_md`, produces markdown with
section headers and item links, and writes the file into a temporary output
folder (`tmp_path`) without touching real project directories.
"""

from pathlib import Path

from app import main
from app.render import render_md as real_render_md


class _FakeAgent:
    def __init__(self, top_n: int = 12):
        self.top_n = top_n

    def top_models(self):
        return [{"id": "org/model-a", "link": "https://huggingface.co/org/model-a", "downloads": 100}]

    def trending_datasets(self):
        return [{"id": "org/dataset-a", "link": "https://huggingface.co/datasets/org/dataset-a", "likes": 10}]

    def trending_spaces(self):
        return [{"id": "org/space-a", "link": "https://huggingface.co/spaces/org/space-a", "likes": 5}]

    def summarize_items(self, section_name, items):
        return f"summary for {section_name}" if items else None


def test_main_renders_expected_sections_and_links(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DailyHuggingFaceAgent", _FakeAgent)
    monkeypatch.setattr(main, "_today_kst_str", lambda: "2026-01-02")
    monkeypatch.setenv("NEWSLETTER_OUTPUT_DIR", str(tmp_path))

    captured = {}

    def _capture_render_md(models, datasets, spaces, summaries, date_str, out_path):
        md = real_render_md(models, datasets, spaces, summaries, date_str=date_str, out_path=out_path)
        captured["md"] = md
        captured["out_path"] = out_path
        return md

    monkeypatch.setattr(main, "render_md", _capture_render_md)

    main.main()

    assert "## Trending Models" in captured["md"]
    assert "## Trending Datasets" in captured["md"]
    assert "## Trending Spaces" in captured["md"]
    assert "- [org/model-a](https://huggingface.co/org/model-a)" in captured["md"]
    assert "- [org/dataset-a](https://huggingface.co/datasets/org/dataset-a)" in captured["md"]
    assert "- [org/space-a](https://huggingface.co/spaces/org/space-a)" in captured["md"]

    output_file = Path(captured["out_path"])
    assert output_file.parent == tmp_path
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == captured["md"]
