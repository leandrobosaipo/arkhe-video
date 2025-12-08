# Comandos para Workflow Trim + Caption

Este documento descreve o workflow completo para cortar um vídeo para 7 segundos e adicionar legendas personalizadas (headline + CTA).

## Passo 1: Cortar Vídeo para 7 Segundos

Use o endpoint `/v1/video/trim` para cortar o vídeo mantendo apenas os primeiros 7 segundos.

```bash
curl -X POST 'http://localhost:8080/v1/video/trim' \
  -H 'accept: application/json' \
  -H 'x-api-key: dev-key-123456' \
  -H 'Content-Type: application/json' \
  -d '{
  "video_url": "https://cod5.nyc3.digitaloceanspaces.com/upload/reframe/2025/12/04/9e0fc9c6dd9d4c27ac485b36ed356b03.MP4",
  "start": "00:00:00.000",
  "end": "00:00:07.000",
  "webhook_url": "https://criadordigital-n8n-webhook.easypanel.codigo5.com.br/webhook/video-trimmed",
  "id": "trim-video-7s-001"
}'
```

**Resposta esperada:**
```json
{
  "code": 202,
  "job_id": "...",
  "message": "processing",
  ...
}
```

**Importante:** Guarde a URL retornada no campo `response` após o processamento concluir. Esta será a `video_url` usada no próximo passo.

## Passo 2: Adicionar Legendas Personalizadas (Headline + CTA)

Use o endpoint `/v1/video/caption` para adicionar legendas com fundo branco e texto preto.

### Preparação do SRT para CTA aos 7 segundos

Para adicionar o CTA "leia a legenda" aos 7 segundos, você precisa:

1. **Opção A:** Modificar o arquivo SRT para incluir uma entrada começando em `00:00:07.000`:
   ```
   3
   00:00:07.000 --> 00:00:10.000
   leia a legenda
   ```

2. **Opção B:** Usar `exclude_time_ranges` para remover legendas após 7s e adicionar o CTA manualmente no SRT antes de enviar.

### Comando para Adicionar Legendas

```bash
curl -X POST 'http://localhost:8080/v1/video/caption' \
  -H 'accept: application/json' \
  -H 'x-api-key: dev-key-123456' \
  -H 'Content-Type: application/json' \
  -d '{
  "video_url": "URL_DO_VIDEO_CORTADO_DO_PASSO_1",
  "subtitles_url": "https://cod5.nyc3.digitaloceanspaces.com/upload/reframe/2025/12/04/7bc1a2e871e147ebad3923f32cd82939.srt",
  "position": {
    "position": "bottom_center"
  },
  "style": {
    "font_family": "Arial",
    "font_size": 42,
    "font_color": "#000000",
    "background_color": "#FFFFFF",
    "outline_color": "#000000",
    "outline_width": 2,
    "alignment": "center",
    "bold": false,
    "italic": false
  },
  "webhook_url": "https://criadordigital-n8n-webhook.easypanel.codigo5.com.br/webhook/video-with-headline",
  "id": "caption-headline-cta-001"
}'
```

**Notas importantes:**
- `font_color: "#000000"` = texto preto
- `background_color: "#FFFFFF"` = fundo branco
- O mapeamento automático converte `font_color` → `line_color` e `background_color` → `box_color` internamente
- A posição `bottom_center` coloca as legendas mais abaixo no vídeo (aproximadamente 85.7% da altura)
- O encoding UTF-8 está habilitado por padrão para suportar caracteres especiais

## Workflow Completo em Sequência

1. Execute o comando de trim e aguarde a conclusão
2. Copie a URL do vídeo cortado do campo `response`
3. Modifique o SRT para incluir o CTA aos 7 segundos (se necessário)
4. Execute o comando de caption usando a URL do vídeo cortado
5. Aguarde a conclusão e obtenha o vídeo final com legendas

## Exemplo de SRT com CTA

```
1
00:00:00.000 --> 00:00:03.000
Primeira legenda da headline

2
00:00:03.000 --> 00:00:06.000
Segunda legenda da headline

3
00:00:07.000 --> 00:00:10.000
leia a legenda
```

