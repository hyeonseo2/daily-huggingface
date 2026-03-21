import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .agent import DailyHuggingFaceAgent
from .render import render_md

TOP = int(os.getenv("NEWSLETTER_TOP_N", "12"))
BLOG_TOP_N = int(os.getenv("NEWSLETTER_BLOG_TOP_N", "5"))


def _today_kst_str():
    kst = timezone(timedelta(hours=9))
    return datetime.now(tz=kst).date().isoformat()


def main():
    date_str = _today_kst_str()
    agent = DailyHuggingFaceAgent(top_n=TOP)

    models = agent.top_models()
    datasets = agent.trending_datasets()
    spaces = agent.trending_spaces()
    blogs = agent.latest_blogs(limit=BLOG_TOP_N)
    papers = agent.daily_papers(date=date_str)

    summaries = {
        "models": agent.summarize_items("models", models),
        "datasets": agent.summarize_items("datasets", datasets),
        "spaces": agent.summarize_items("spaces", spaces),
    }

    filename = f"daily-huggingface-{date_str}.md"

    default_out_dir = Path(__file__).resolve().parents[1] / "newsletters"
    out_dir_env = os.getenv("NEWSLETTER_OUTPUT_DIR")
    out_dir = Path(out_dir_env).expanduser() if out_dir_env else default_out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    render_md(
        models,
        datasets,
        spaces,
        summaries,
        date_str=date_str,
        out_path=str(out_path),
        blogs=blogs,
        papers=papers,
    )
    print(f"[daily-huggingface] generated {out_path}")


if __name__ == "__main__":
    main()
