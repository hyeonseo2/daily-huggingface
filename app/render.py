from jinja2 import Template
from typing import List, Dict, Any

MD_TPL = Template("""# Daily HuggingFace — {{ date_str }}

{% if models %}
## Trending Models
{% if models_summary %}> {{ models_summary }}
{% endif %}{% for x in models %}- [{{x._label}}]({{x.link}}){% if x.meta %} — {{x.meta}}{% endif %}
{% endfor %}{% endif %}

{% if datasets %}
## Trending Datasets
{% if datasets_summary %}> {{ datasets_summary }}
{% endif %}{% for x in datasets %}- [{{x._label}}]({{x.link}}){% if x.meta %} — {{x.meta}}{% endif %}
{% endfor %}{% endif %}

{% if spaces %}
## Trending Spaces
{% if spaces_summary %}> {{ spaces_summary }}
{% endif %}{% for x in spaces %}- [{{x._label}}]({{x.link}}){% if x.meta %} — {{x.meta}}{% endif %}
{% endfor %}{% endif %}

{% if papers %}
## Latest Papers
{% for x in papers %}- [{{x._label}}]({{x.link}}){% if x.meta %} — {{x.meta}}{% endif %}
{% endfor %}{% endif %}

{% if blogs %}
## Latest Blogs
{% for x in blogs %}- [{{x._label}}]({{x.link}}){% if x.meta %} — {{x.meta}}{% endif %}
{% endfor %}{% endif %}
""")


def _fmt_meta(x: Dict[str, Any], section: str) -> str:
    m = []

    # Papers/Blogs: keep only upvotes
    if section in {"blogs", "papers"}:
        if x.get("upvotes") is not None:
            m.append(f"👍 {x['upvotes']}")
        return " • ".join(m)

    # Models/Datasets/Spaces
    if x.get("downloads") is not None:
        m.append(f"⬇️ {x['downloads']}")
    if x.get("likes") is not None:
        m.append(f"❤️ {x['likes']}")
    if x.get("upvotes") is not None:
        m.append(f"👍 {x['upvotes']}")
    if x.get("library"):
        m.append(f"📚 {x['library']}")
    if x.get("publishedAt") is not None and not x.get("id", "").startswith("org/") and "/" in x.get("link", ""):
        m.append(f"🗓 {x['publishedAt'][:10]}")
    if x.get("authors") and isinstance(x.get("authors"), list):
        authors = x["authors"]
        if len(authors) > 0:
            head = authors[:2]
            if isinstance(head[0], str):
                m.append("✍️ " + ", ".join(head))

    return " • ".join(m)


def _attach_meta(models, datasets, spaces, blogs, papers):
    for x in models:
        x["meta"] = _fmt_meta(x, section="models")
        x["_label"] = x.get("title") or x["id"]

    for x in datasets:
        x["meta"] = _fmt_meta(x, section="datasets")
        x["_label"] = x.get("title") or x["id"]

    for x in spaces:
        x["meta"] = _fmt_meta(x, section="spaces")
        x["_label"] = x.get("title") or x["id"]

    for x in blogs:
        x["meta"] = _fmt_meta(x, section="blogs")
        x["_label"] = x.get("title") or x["id"]

    for x in papers:
        x["meta"] = _fmt_meta(x, section="papers")
        x["_label"] = x.get("title") or x["id"]


def render_md(models, datasets, spaces, summaries, date_str: str, out_path: str, blogs=None, papers=None):
    blogs = blogs or []
    papers = papers or []

    _attach_meta(models, datasets, spaces, blogs, papers)

    md = MD_TPL.render(
        date_str=date_str,
        models=models,
        datasets=datasets,
        spaces=spaces,
        blogs=blogs,
        papers=papers,
        models_summary=summaries.get("models"),
        datasets_summary=summaries.get("datasets"),
        spaces_summary=summaries.get("spaces"),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    return md
