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

    def latest_blogs(self, limit: int = 5):
        return [{"id": "blog-a", "title": "Latest Blog A", "link": "https://huggingface.co/blog/blog-a", "upvotes": 21}]

    def daily_papers(self, date: str, limit: int = 12):
        return [{"id": "2401.12345", "title": "Paper A", "link": "https://huggingface.co/papers/2401.12345", "upvotes": 12}]

    def summarize_items(self, section_name, items):
        return f"summary for {section_name}" if items else None


def test_main_renders_expected_sections_and_links(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DailyHuggingFaceAgent", _FakeAgent)
    monkeypatch.setenv("NEWSLETTER_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("NEWSLETTER_BLOG_TOP_N", "2")
    monkeypatch.setattr(main, "_today_kst_str", lambda: "2026-01-02")

    captured = {}

    def _capture_render_md(models, datasets, spaces, summaries, date_str, out_path, blogs=None, papers=None):
        md = real_render_md(
            models,
            datasets,
            spaces,
            summaries,
            date_str=date_str,
            out_path=out_path,
            blogs=blogs,
            papers=papers,
        )
        captured["md"] = md
        captured["out_path"] = out_path
        return md

    monkeypatch.setattr(main, "render_md", _capture_render_md)

    main.main()

    assert "## Trending Models" in captured["md"]
    assert "## Trending Datasets" in captured["md"]
    assert "## Trending Spaces" in captured["md"]
    # order check
    assert captured["md"].index("## Latest Papers") < captured["md"].index("## Latest Blogs")
    assert "## Latest Blogs" in captured["md"]
    assert "## Latest Papers" in captured["md"]

    assert "- [org/model-a](https://huggingface.co/org/model-a)" in captured["md"]
    assert "- [org/dataset-a](https://huggingface.co/datasets/org/dataset-a)" in captured["md"]
    assert "- [org/space-a](https://huggingface.co/spaces/org/space-a)" in captured["md"]
    assert "- [Latest Blog A](https://huggingface.co/blog/blog-a)" in captured["md"]
    assert "- [Paper A](https://huggingface.co/papers/2401.12345)" in captured["md"]

    # blogs and papers should show only upvotes metadata
    assert "👍 12" in captured["md"]  # paper
    assert "👍 21" in captured["md"]  # blog
    # no extra metrics for papers/blogs
    assert "⬇️" not in "\n".join([line for line in captured["md"].splitlines() if "Paper A" in line or "Latest Blog A" in line])

    output_file = Path(captured["out_path"])
    assert output_file.parent == tmp_path
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == captured["md"]
