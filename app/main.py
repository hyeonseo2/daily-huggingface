# app/main.py
import os
from datetime import datetime, timezone, timedelta

from .agent import DailyHuggingFaceAgent
from .render import render_md

TOP = int(os.getenv("NEWSLETTER_TOP_N", "12"))

def _today_kst_str():
    kst = timezone(timedelta(hours=9))
    return datetime.now(tz=kst).date().isoformat()

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

    # 컨테이너 내부 출력 경로
    out_dir = "/data"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    render_md(models, datasets, spaces, summaries, date_str=date_str, out_path=out_path)
    print(f"[daily-huggingface] generated {out_path}")

if __name__ == "__main__":
    main()
