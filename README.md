# 📰 Daily HuggingFace

🇰🇷 한국어 README: [README.ko.md](./README.ko.md)

Daily HuggingFace generates a Markdown newsletter with trending Hugging Face models, datasets, and spaces.

- Default output directory: `newsletters/`
- Configurable via `NEWSLETTER_OUTPUT_DIR`
- Supports Hugging Face REST API and Hugging Face MCP (`hub_repo_search`)
- Scheduled run supported via GitHub Actions
- Output file format: `daily-huggingface-YYYY-MM-DD.md`

---

## Contents

- [What is this](#what-is-this)
- [Quick start](#quick-start)
- [MCP setup (important)](#mcp-setup-important)
- [Environment Variables](#environment-variables)
- [Docker Compose](#docker-compose)
- [GitHub Actions](#github-actions)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Output example](#output-example)
- [Changelog / extension ideas](#changelog--extension-ideas)

---

## What is this

This app creates a daily Markdown newsletter summarizing:

- **Trending Models**
- **Trending Datasets**
- **Trending Spaces**

It applies recency-first prioritization and fallback to REST API when MCP is unavailable.

---

## Quick start

### 1) Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

HF_TOKEN=hf_xxx python3 -m app.main
```

Default output:

```text
<repo>/newsletters/daily-huggingface-YYYY-MM-DD.md
```

Override output path:

```bash
NEWSLETTER_OUTPUT_DIR=/tmp/out python3 -m app.main
```

### 2) Run with Docker

```bash
docker build -t daily-huggingface .
mkdir -p out
docker run --rm \
  -e HF_TOKEN="hf_xxxxx" \
  -e NEWSLETTER_OUTPUT_DIR="/data" \
  -v "$(pwd)/out:/data" \
  -e MCP_URL="https://huggingface.co/mcp" \
  daily-huggingface
```

> `tmp` directories in repository should be ignored by output path for local test runs.

---

## MCP setup (important)

### Endpoint

Use MCP server endpoint:

- `https://huggingface.co/mcp`

In this project, MCP tool name is **`hub_repo_search`**.

### Why this matters

- This repo's MCP integration is implemented against HF MCP `hub_repo_search`.
- Older docs/examples may show different tool names.

### Quick connection check (optional)

```bash
curl -sS -X POST https://huggingface.co/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"daily-hf","version":"1.0"},"capabilities":{}}}'
```

Then query tools and try a sample search with `repo_types`.

---

## Environment Variables

| Name | Description | Required | Default |
| --- | --- | --- | --- |
| `HF_TOKEN` | Hugging Face token (rate limit relief/private access) | optional | (empty) |
| `MCP_URL` | MCP endpoint (recommended `https://huggingface.co/mcp`) | optional | empty |
| `NEWSLETTER_OUTPUT_DIR` | Output directory | optional | `newsletters/` |
| `OPENAI_API_KEY` | Optional OpenAI key for section summaries | optional | empty |
| `NEWSLETTER_TOP_N` | Number of items per section | optional | `12` |
| `TZ` | Timezone | optional | `Asia/Seoul` |

---

## Docker Compose

```yaml
version: "3.9"
services:
  daily-huggingface:
    build: .
    container_name: daily-huggingface
    environment:
      HF_TOKEN: "${HF_TOKEN}"
      MCP_URL: "${MCP_URL}"
      OPENAI_API_KEY: "${OPENAI_API_KEY}"
      NEWSLETTER_TOP_N: "12"
      NEWSLETTER_OUTPUT_DIR: "/data"
      TZ: "Asia/Seoul"
    volumes:
      - ./out:/data
    restart: "no"
```

Run:

```bash
HF_TOKEN=hf_xxxxxx MCP_URL=https://huggingface.co/mcp docker compose up --build
```

---

## GitHub Actions

Workflow file: `.github/workflows/daily-huggingface.yml`

- Schedule: `0 23 * * *` (KST 08:00)
- Two-step pipeline:
  1. Generate newsletter (`python -m app.main`)
  2. Create issue with generation summary
- Optional artifact mode: set repository variable `REPORT_WITH_ARTIFACT=true`

---

## Testing

```bash
pytest -q
```

Current tests cover MCP preference, recentness + fallback logic, and end-to-end rendering.

---

## Troubleshooting

- If MCP returns session-related errors:
  - Ensure `Accept: application/json, text/event-stream`
  - Ensure session flow is handled by `mcp-session-id`
- If you see `hf_api.trending(...)` errors but output is still generated:
  - This is expected fallback behavior (REST fallback/retry path)
- If a link format differs (`hf.co/...`), this is expected and valid

---

## Output example

```markdown
# Daily HuggingFace — 2026-03-16

## Trending Models
- [meta-llama/Llama-3.1-8B](https://huggingface.co/meta-llama/Llama-3.1-8B) — ⬇️ 12345 • ❤️ 678 • 📚 transformers

## Trending Datasets
- [squad](https://huggingface.co/datasets/squad) — ⬇️ 100000 • ❤️ 1000

## Trending Spaces
- [stabilityai/stable-diffusion-demo](https://huggingface.co/spaces/stabilityai/stable-diffusion-demo) — ❤️ 2000
```

---

## Changelog / extension ideas

- Add weekly delta ranking
- Add domain filtering (vision/nlp/audio)
- Add Hugging Face blog/paper sections
- Add publication targets (Slack, Discord, Notion, email)

---

## Korean README

For Korean instructions, use:

- `README.ko.md`
