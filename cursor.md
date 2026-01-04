# transformers serve 클라이언트로서 Cursor 사용하기

이 예시는 인기 있는 IDE인 [Cursor](https://cursor.com/)에 대해 `transformers serve`를 로컬 LLM 공급자로 사용하는 방법을 보여줍니다. 이 특정 경우, `transformers serve`에 대한 요청은 외부 IP (Cursor의 서버 IP)에서 오게 되므로 추가 설정이 필요합니다. 게다가 Cursor의 일부 요청은 보안상의 이유로 기본적으로 비활성화된 [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)가 필요합니다.

CORS가 활성화된 서버를 시작하려면 다음을 실행하세요.

```shell
transformers serve --enable-cors
```

또한 서버를 외부 IP에 노출해야 합니다. 가능한 해결책은 자유로운 무료 플랜을 제공하는 [`ngrok`](https://ngrok.com/)을 사용하는 것입니다. `ngrok` 계정을 설정하고 서버 머신에서 인증을 마친 후, 다음을 실행합니다.

```shell
ngrok http [port]
```

여기서 `port`는 `transformers serve`가 사용하는 포트로 기본값은 `8000`입니다. `ngrok`을 실행한 터미널에서 아래 그림과 같이 "Forwarding" 행에 https 주소가 나타납니다. 이 주소가 요청을 보낼 주소입니다.

<h3 align="center">
    <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/transformers_serve_ngrok.png"/>
</h3>

이제 앱 쪽 설정을 할 준비가 되었습니다! Cursor에서는 새 공급자를 설정할 수는 없지만, 모델 선택 설정에서 OpenAI 요청의 엔드포인트를 변경할 수 있습니다. 먼저 "Settings" > "Cursor Settings"에서 "Models" 탭으로 가서 "API Keys" 접기 메뉴를 확장하세요. `transformers serve` 엔드포인트를 설정하려면 다음 절차를 따르세요:

1. 위 목록에서 모든 모델을 선택 해제합니다 (예: `gpt4` 등);
2. 사용하려는 모델을 추가하고 선택합니다 (예: `Qwen/Qwen3-4B`);
3. OpenAI API Key 필드에 임의의 텍스트를 입력하세요. 이 필드는 사용되지 않지만 비어 있을 수 없습니다;
4. `ngrok`에서 받은 https 주소를 "Override OpenAI Base URL" 필드에 추가하고 주소 끝에 `/v1`을 덧붙입니다 (예: `https://(...).ngrok-free.app/v1`);
5. "Verify" 버튼을 누르세요.

이 단계를 따르면 "Models" 탭이 아래 이미지처럼 보일 것입니다. 서버도 검증 단계에서 몇 번의 요청을 받은 상태여야 합니다.

<h3 align="center">
    <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/transformers_serve_cursor.png"/>
</h3>

이제 Cursor에서 로컬 모델을 사용할 준비가 되었습니다! 예를 들어, AI Pane을 켜면 추가한 모델을 선택하고 로컬 파일에 대해 모델에게 질문할 수 있습니다.

<h3 align="center">
    <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/transformers_serve_cursor_chat.png"/>
</h3>
