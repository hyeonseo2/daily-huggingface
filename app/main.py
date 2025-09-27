# app/main.py
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .agent import DailyHuggingFaceAgent
from .render import render_md

TOP = int(os.getenv("NEWSLETTER_TOP_N", "12"))

def _today_kst_str():
    kst = timezone(timedelta(hours=9))
    return datetime.now(tz=kst).date().isoformat()

def _resolve_output_dir(out_dir_env: str | None) -> Path:
    """Return the configured output directory.

    If ``NEWSLETTER_OUTPUT_DIR`` is set and relative, treat it as relative to the
    repository root (i.e. alongside this file). Otherwise default to
    ``<repo>/newsletters``.
    """

    repo_root = Path(__file__).resolve().parents[1]

    if out_dir_env:
        candidate = Path(out_dir_env).expanduser()
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        return candidate

    return repo_root / "newsletters"


def main():
    agent = DailyHuggingFaceAgent(top_n=TOP)

    models   = agent.top_models()
    datasets = agent.trending_datasets()
    spaces   = agent.trending_spaces()

    summaries = {
        "models": agent.summarize_items("models", models),
        "datasets": agent.summarize_items("datasets", datasets),
        "spaces": agent.summarize_items("spaces", spaces),
    }

    date_str = _today_kst_str()
    filename = f"daily-huggingface-{date_str}.md"

    out_dir = _resolve_output_dir(os.getenv("NEWSLETTER_OUTPUT_DIR"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    render_md(models, datasets, spaces, summaries, date_str=date_str, out_path=str(out_path))
    print(f"[daily-huggingface] generated {out_path}")

if __name__ == "__main__":
    main()
