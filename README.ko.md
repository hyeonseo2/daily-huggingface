# 📰 Daily HuggingFace

🇺🇸 English README: [README.md](./README.md)

Hugging Face의 **인기 모델 / 트렌딩 데이터셋 / 트렌딩 스페이스**를 매일 수집해
Markdown 뉴스레터(`daily-huggingface-YYYY-MM-DD.md`)로 만드는 프로젝트입니다.

- 기본 데이터 소스: Hugging Face REST API
- 선택 데이터 소스: Hugging Face MCP (`hub_repo_search`)
- 기본 출력: `newsletters/`
- `NEWSLETTER_OUTPUT_DIR`으로 출력 위치 변경 가능

---

## 핵심 기능

- 모델/데이터셋/스페이스 수집
- MCP가 가능하면 MCP(`hub_repo_search`) 우선 사용
- MCP 실패/부족 시 REST API(`trending`, `recent`, `top_*`)로 폴백
- 최근 7일 항목 우선 정렬 + 점수 보정
- 선택적으로 OpenAI 요약 생성

---

## 빠른 시작

### 1) 로컬 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

HF_TOKEN=hf_xxx python3 -m app.main
```

기본 출력:

```text
<repo>/newsletters/daily-huggingface-YYYY-MM-DD.md
```

출력 경로 변경:

```bash
NEWSLETTER_OUTPUT_DIR=/tmp/out python3 -m app.main
```

### 2) Docker 실행

```bash
docker build -t daily-huggingface .
mkdir -p out
docker run --rm \
  -e HF_TOKEN="hf_xxxxx" \
  -e MCP_URL="https://huggingface.co/mcp" \
  -e NEWSLETTER_OUTPUT_DIR="/data" \
  -v "$(pwd)/out:/data" \
  daily-huggingface
```

---

## MCP 설정 (중요)

### MCP URL

권장 값:

- `https://huggingface.co/mcp`

### MCP 툴명

이 프로젝트는 공식 Hugging Face MCP의 다음 툴을 사용합니다.

- `hub_repo_search`

(`hub.search`가 아니라 `hub_repo_search` 사용)

### 간단 연결 체크

```bash
curl -sS -X POST https://huggingface.co/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"daily-hf","version":"1.0"},"capabilities":{}}}'
```

세션이 필요하면 응답 헤더의 `mcp-session-id`를 받아 이어서 호출하면 됩니다.

`query: "*"`는 MCP 동작에 따라 빈 쿼리로 정규화되어 처리됩니다.

---

## 환경 변수

| 변수 | 설명 | 필수 | 기본 |
| --- | --- | --- | --- |
| `HF_TOKEN` | Hugging Face 토큰(레이트리밋 완화) | 선택 | 없음 |
| `MCP_URL` | MCP 엔드포인트(권장 `https://huggingface.co/mcp`) | 선택 | 없음 |
| `NEWSLETTER_OUTPUT_DIR` | 출력 폴더 | 선택 | `newsletters/` |
| `OPENAI_API_KEY` | 섹션 요약용 API 키 | 선택 | 없음 |
| `NEWSLETTER_TOP_N` | 섹션별 개수 | 선택 | `12` |
| `TZ` | 타임존 | 선택 | `Asia/Seoul` |

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

실행:

```bash
HF_TOKEN=hf_xxxxxx MCP_URL=https://huggingface.co/mcp docker compose up --build
```

---

## GitHub Actions

- 워크플로우: `.github/workflows/daily-huggingface.yml`
- 스케줄: `0 23 * * *` (KST 08:00)
- 단계
  1. `python -m app.main` 실행으로 뉴스레터 생성
  2. Issue 생성으로 결과 보고
- 옵션: `vars.REPORT_WITH_ARTIFACT=true` 설정 시 artifact 업로드

---

## 테스트

```bash
pytest -q
```

기능 테스트 범위: MCP 우선 수집, 최근성 정렬, 폴백 로직, 최종 렌더링.

---

## 문제해결

- MCP 세션 관련 에러 발생 시
  - `Accept: application/json, text/event-stream` 사용 여부 확인
  - `mcp-session-id` 재사용 여부 확인
- REST API 에러가 나더라도 기본 결과 생성되면 정상(폴백 동작)
- 링크가 `hf.co/...` 형태로 출력되어도 정상입니다

---

## 결과물 예시

`daily-huggingface-2026-03-16.md`

```markdown
# Daily HuggingFace — 2026-03-16

## Trending Models
- [meta-llama/Llama-3.1-8B](https://huggingface.co/meta-llama/Llama-3.1-8B) — downloads: 12345, likes: 678, lib: transformers

## Trending Datasets
- [squad](https://huggingface.co/datasets/squad) — downloads: 100000, likes: 1000

## Trending Spaces
- [stabilityai/stable-diffusion-demo](https://huggingface.co/spaces/stabilityai/stable-diffusion-demo) — likes: 2000
```

---

## 개선 아이디어

- 주간 대비 증감률
- 카테고리/태그 필터(CV/NLP/Audio)
- 블로그/논문 섹션 추가
- 외부 채널 게시 자동화(Discord/Slack/Notion)
