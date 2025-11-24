# Payloads para Teste no Swagger

## Como Testar

1. Acesse: `https://arkhe-video.mhcqvd.easypanel.host/apidocs/`
2. Clique em **"Authorize"** (cadeado no topo)
3. Cole a API Key: `73877c79cfdab3ab8afcc6cbf6c774719af6ea6f85bfe45f728e06a2c773a5f3`
4. Expanda a seção **"Media"**
5. Clique em **POST /v1/media/transcribe**
6. Clique em **"Try it out"**
7. Cole um dos payloads abaixo
8. Clique em **"Execute"**

## Payload 1: Teste Mínimo (Caso que estava falhando)

Este é o caso que estava gerando erro. Teste este primeiro para validar a correção:

```json
{
  "media_url": "https://cod5.nyc3.digitaloceanspaces.com/upload/reframe/2025/11/24/f95899208501492eb5e39bb241232585.mp4",
  "include_text": true,
  "include_srt": false,
  "include_segments": false,
  "response_type": "direct",
  "language": "pt"
}
```

**O que verificar:**
- Status deve ser 200 (sucesso) ou 202 (enfileirado)
- Se 200, a resposta deve conter `"text"` com o texto transcrito
- Não deve aparecer erro "Object of type bytes is not JSON serializable"

## Payload 2: Teste com Segments

Para validar que a correção anterior de segments também funciona:

```json
{
  "media_url": "https://cod5.nyc3.digitaloceanspaces.com/upload/reframe/2025/11/24/f95899208501492eb5e39bb241232585.mp4",
  "include_text": true,
  "include_srt": false,
  "include_segments": true,
  "response_type": "direct",
  "language": "pt"
}
```

**O que verificar:**
- Status deve ser 200 ou 202
- Se 200, a resposta deve conter `"segments"` como array
- Cada segmento deve ter campos: `id`, `start`, `end`, `text`
- Não deve conter objetos bytes

## Payload 3: Teste Completo (Com Webhook)

Este é o payload completo que você estava usando:

```json
{
  "media_url": "https://cod5.nyc3.digitaloceanspaces.com/upload/reframe/2025/11/24/f95899208501492eb5e39bb241232585.mp4",
  "task": "transcribe",
  "include_text": true,
  "include_srt": false,
  "include_segments": false,
  "word_timestamps": false,
  "response_type": "direct",
  "language": "pt",
  "webhook_url": "https://projetocortes-n8n-webhook.mhcqvd.easypanel.host/webhook/pos_transcribe",
  "words_per_line": 8,
  "id": "custom-request-id"
}
```

**O que verificar:**
- Status deve ser 200 ou 202
- Se 202, significa que foi enfileirado e o webhook será chamado quando concluir
- Se 200, resposta direta com texto transcrito

## Payload 4: Teste com SRT

Para testar se srt_text também está sendo tratado corretamente:

```json
{
  "media_url": "https://cod5.nyc3.digitaloceanspaces.com/upload/reframe/2025/11/24/f95899208501492eb5e39bb241232585.mp4",
  "include_text": true,
  "include_srt": true,
  "include_segments": false,
  "response_type": "direct",
  "language": "pt"
}
```

**O que verificar:**
- Status deve ser 200 ou 202
- Se 200, a resposta deve conter `"srt"` com conteúdo SRT válido
- Não deve conter bytes

## Respostas Esperadas

### Sucesso (200):
```json
{
  "code": 200,
  "endpoint": "/v1/transcribe/media",
  "job_id": "uuid-aqui",
  "message": "success",
  "response": {
    "text": "Texto transcrito aqui...",
    "srt": null,
    "segments": null,
    "text_url": null,
    "srt_url": null,
    "segments_url": null
  },
  "build_number": 211
}
```

### Enfileirado (202):
```json
{
  "code": 202,
  "job_id": "uuid-aqui",
  "message": "processing",
  "queue_length": 1
}
```

### Erro (500):
Se ainda houver erro, você verá:
```json
{
  "message": "Internal Server Error"
}
```

Neste caso, verifique os logs do servidor para ver o erro completo.

## Troubleshooting

### Se receber erro 500:
1. Verifique se a URL do vídeo está acessível
2. Verifique os logs do servidor para ver o erro completo
3. Tente com um vídeo menor primeiro

### Se receber 202 (enfileirado):
- Isso é normal quando há `webhook_url`
- O processamento acontece em background
- O resultado será enviado para o webhook quando concluir
- Você pode verificar o status usando `/v1/toolkit/job/status` com o `job_id`

