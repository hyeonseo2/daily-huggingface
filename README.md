# 📰 Daily HuggingFace

매일 Hugging Face의 **인기 모델 / 트렌딩 데이터셋 / 트렌딩 스페이스**를 모아
Markdown 뉴스레터 파일(`daily-huggingface-YYYY-MM-DD.md`)을 생성합니다. 기본적으로
`app.main`은 리포지토리의 `newsletters/` 디렉터리에 파일을 저장하며, 환경 변수
`NEWSLETTER_OUTPUT_DIR`로 다른 경로로 변경할 수 있습니다.

- **기본 데이터 소스**: Hugging Face REST API
- **선택적으로** Hugging Face MCP 서버(`MCP_URL`)를 함께 사용
- **로컬 / Docker 실행**으로 수동 생성 가능
- **GitHub Actions 워크플로우**를 통해 매일 자동 실행 + Pull Request 생성 가능

---

## 🚀 빠른 시작

### 1. Docker 빌드
```bash
git clone https://github.com/yourname/daily-huggingface.git
cd daily-huggingface
docker build -t daily-huggingface .
````

### 2. 실행

```bash
# 결과는 ./out/daily-huggingface-YYYY-MM-DD.md 로 생성
mkdir -p out
docker run --rm \
  -e HF_TOKEN="hf_xxxxxxxxx" \
  -e NEWSLETTER_OUTPUT_DIR="/data" \
  -v "$(pwd)/out:/data" \
  daily-huggingface
```

### 3. 스모크 테스트

빠르게 동작 확인을 하고 싶다면:

```bash
docker run --rm \
  -e HF_TOKEN="hf_xxxxxxxxx" \
  -e NEWSLETTER_OUTPUT_DIR="/data" \
  -v "$(pwd)/out:/data" \
  --entrypoint python \
  daily-huggingface -m app.smoke_test
```

출력 예시:

```
=== Daily HuggingFace Smoke Test ===
HF_TOKEN set? YES
MCP_URL set?  NO
TOP_N: 6
Output: /data/_test-daily-huggingface-2025-09-26.md
Models:   6
Datasets: 6
Spaces:   6

-- Models (top 3) --
- meta-llama/Llama-3.1-8B ...
...
```

---

## ⚙️ 환경 변수

| 이름                 | 설명                                 | 필수 | 기본         |
| ------------------ | ---------------------------------- | -- | ---------- |
| `HF_TOKEN`         | Hugging Face 토큰 (레이트리밋 완화/프라이빗 접근) | 선택 | 없음         |
| `MCP_URL`          | Hugging Face MCP 서버 `/mcp` 엔드포인트   | 선택 | 없음         |
| `NEWSLETTER_OUTPUT_DIR` | 뉴스레터 파일 출력 디렉터리              | 선택 | `newsletters/` |
| `OPENAI_API_KEY`   | OpenAI API 키 (요약문 생성에 사용)          | 선택 | 없음         |
| `NEWSLETTER_TOP_N` | 섹션별 항목 수                           | 선택 | 12         |
| `TZ`               | 타임존                                | 선택 | Asia/Seoul |

---

## 📦 docker-compose

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
HF_TOKEN=hf_xxxxxxxxx docker compose up --build
```

---

## 🤖 GitHub Actions 자동화

리포지토리에 포함된 워크플로우 파일:
`.github/workflows/daily-huggingface.yml`

* 매일 **KST 08:00** 실행
* 뉴스레터 파일 생성 → `newsletters/` 폴더에 추가 → **자동 PR 생성**

### Secrets 설정

* `HF_TOKEN` (권장)
* `MCP_URL` (옵션)
* `OPENAI_API_KEY` (옵션)

---

## 📂 결과물 예시

`daily-huggingface-2025-09-26.md`

```markdown
# Daily HuggingFace — 2025-09-26

## Top Models
- [meta-llama/Llama-3.1-8B](https://huggingface.co/meta-llama/Llama-3.1-8B) — downloads: 12345, likes: 678, lib: transformers
- [openai/clip-vit-base-patch32](https://huggingface.co/openai/clip-vit-base-patch32) — downloads: 54321, likes: 789

## Trending Datasets
- [squad](https://huggingface.co/datasets/squad) — downloads: 100000, likes: 1000

## Trending Spaces
- [stabilityai/stable-diffusion-demo](https://huggingface.co/spaces/stabilityai/stable-diffusion-demo) — likes: 2000
```

---

## 🛠️ 확장 아이디어

* 지난주 대비 증감률 / 분야별 필터(CV, NLP 등)
* Hugging Face 블로그 포스트 섹션 추가
* 스페이스 실행 결과(이미지/오디오) 링크 포함(MCP 활용)
* 이메일/Slack/Notion 자동 게시 파이프라인 추가