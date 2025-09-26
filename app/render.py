# app/render.py
from jinja2 import Template
from typing import List, Dict, Any

MD_TPL = Template("""# Daily HuggingFace — {{ date_str }}

{% if models %}
## Top Models
{% if models_summary %}> {{ models_summary }}
{% endif %}{% for x in models %}- [{{x.id}}]({{x.link}}){% if x.meta %} — {{x.meta}}{% endif %}
{% endfor %}{% endif %}

{% if datasets %}
## Trending Datasets
{% if datasets_summary %}> {{ datasets_summary }}
{% endif %}{% for x in datasets %}- [{{x.id}}]({{x.link}}){% if x.meta %} — {{x.meta}}{% endif %}
{% endfor %}{% endif %}

{% if spaces %}
## Trending Spaces
{% if spaces_summary %}> {{ spaces_summary }}
{% endif %}{% for x in spaces %}- [{{x.id}}]({{x.link}}){% if x.meta %} — {{x.meta}}{% endif %}
{% endfor %}{% endif %}
""")

def _fmt_meta(x: Dict[str, Any]) -> str:
    m=[]
    if x.get("downloads"): m.append(f"downloads: {x['downloads']}")
    if x.get("likes"):     m.append(f"likes: {x['likes']}")
    if x.get("library"):   m.append(f"lib: {x['library']}")
    return ", ".join(m)

def render_md(models, datasets, spaces, summaries, date_str: str, out_path: str):
    for col in (models, datasets, spaces):
        for x in col:
            x["meta"] = _fmt_meta(x)
    md = MD_TPL.render(
        date_str=date_str,
        models=models, datasets=datasets, spaces=spaces,
        models_summary=summaries.get("models"),
        datasets_summary=summaries.get("datasets"),
        spaces_summary=summaries.get("spaces"),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    return md
