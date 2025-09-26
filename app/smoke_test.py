# app/smoke_test.py
"""
Daily HuggingFace 스모크 테스트:
- REST(API)와 (선택) MCP를 통해 모델/데이터셋/스페이스를 가져오고
- /data/_test-daily-huggingface-YYYY-MM-DD.md 로 렌더 후
- 표준 출력에 요약 카운트와 샘플 항목 3개를 찍습니다.
"""

import os
from datetime import datetime, timezone, timedelta

from .agent import DailyHuggingFaceAgent
from .render import render_md

def _today_kst_str():
    kst = timezone(timedelta(hours=9))
    return datetime.now(tz=kst).date().isoformat()

def main():
    top_n = int(os.getenv("NEWSLETTER_TOP_N", "6"))  # 테스트는 기본 6개만
    agent = DailyHuggingFaceAgent(top_n=top_n)

    models   = agent.top_models()
    datasets = agent.trending_datasets()
    spaces   = agent.trending_spaces()

    summaries = {
        "models": agent.summarize_items("models", models),
        "datasets": agent.summarize_items("datasets", datasets),
        "spaces": agent.summarize_items("spaces", spaces),
    }

    date_str = _today_kst_str()
    out_dir = "/data"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"_test-daily-huggingface-{date_str}.md")
    render_md(models, datasets, spaces, summaries, date_str=date_str, out_path=out_path)

    # 콘솔 프린트(요약)
    print("=== Daily HuggingFace Smoke Test ===")
    print(f"HF_TOKEN set? {'YES' if os.getenv('HF_TOKEN') else 'NO'}")
    print(f"MCP_URL set?  {'YES' if os.getenv('MCP_URL') else 'NO'}")
    print(f"TOP_N: {top_n}")
    print(f"Output: {out_path}")
    print(f"Models:   {len(models)}")
    print(f"Datasets: {len(datasets)}")
    print(f"Spaces:   {len(spaces)}")

    def preview(items, name):
        print(f"\n-- {name} (top 3) --")
        for x in (items[:3] if items else []):
            meta = ", ".join([
                f"dl={x.get('downloads')}" if x.get("downloads") is not None else "",
                f"likes={x.get('likes')}" if x.get("likes") is not None else "",
                f"lib={x.get('library')}" if x.get("library") else "",
            ])
            meta = meta.strip(", ").replace(",,", ",")
            print(f"- {x.get('id')} ({meta}) -> {x.get('link')}")
    preview(models, "Models")
    preview(datasets, "Datasets")
    preview(spaces, "Spaces")

if __name__ == "__main__":
    main()
