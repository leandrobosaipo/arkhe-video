# Como Testar a API Arkhe Video

## Pré-requisitos

1. Python 3.10+ instalado
2. Dependências instaladas: `pip install -r requirements.txt`
3. Variável de ambiente `API_KEY` configurada

## Iniciar a API

### Método 1: Python direto (desenvolvimento)

```bash
export API_KEY="sua-chave-aqui"
python app.py
```

A API estará disponível em `http://localhost:8080`

### Método 2: Gunicorn (produção)

```bash
export API_KEY="sua-chave-aqui"
gunicorn -c gunicorn.conf.py app:create_app
```

## Acessar a Documentação Swagger

Após iniciar a API, acesse:

- **Swagger UI**: http://localhost:8080/apidocs/
- **OpenAPI Spec**: http://localhost:8080/apispec.json

## Testar Endpoints

### Usando o script de teste

```bash
./test_api.sh [API_KEY] [BASE_URL]
```

Exemplo:
```bash
./test_api.sh 123456 http://localhost:8080
```

### Usando curl

#### Teste básico da API

```bash
curl -H "x-api-key: sua-chave-aqui" http://localhost:8080/v1/toolkit/test
```

#### Exemplo: Converter mídia para MP3

```bash
curl -X POST "http://localhost:8080/v1/media/convert/mp3" \
  -H "x-api-key: sua-chave-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://example.com/video.mp4"
  }'
```

#### Exemplo: Transcrever áudio/vídeo

```bash
curl -X POST "http://localhost:8080/v1/media/transcribe" \
  -H "x-api-key: sua-chave-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://example.com/video.mp4",
    "task": "transcribe",
    "include_text": true,
    "include_srt": true,
    "response_type": "direct"
  }'
```

#### Exemplo: Dividir vídeo

```bash
curl -X POST "http://localhost:8080/v1/video/split" \
  -H "x-api-key: sua-chave-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "splits": [
      {
        "start": "00:00:00.000",
        "end": "00:00:30.000"
      },
      {
        "start": "00:01:00.000",
        "end": "00:01:30.000"
      }
    ]
  }'
```

## Endpoints Disponíveis

### Toolkit
- `GET /v1/toolkit/test` - Testa se a API está funcionando
- `GET /v1/toolkit/authenticate` - Autentica uma chave de API
- `POST /v1/toolkit/job/status` - Obtém status de um job específico
- `POST /v1/toolkit/jobs/status` - Obtém status de todos os jobs

### Video
- `POST /v1/video/concatenate` - Concatena múltiplos vídeos
- `POST /v1/video/split` - Divide vídeo em segmentos
- `POST /v1/video/cut` - Remove segmentos de um vídeo
- `POST /v1/video/trim` - Corta vídeo (início/fim)
- `POST /v1/video/thumbnail` - Extrai thumbnail de um vídeo
- `POST /v1/video/caption` - Adiciona legendas a um vídeo

### Audio
- `POST /v1/audio/concatenate` - Concatena múltiplos arquivos de áudio

### Media
- `POST /v1/media/convert` - Converte mídia entre formatos
- `POST /v1/media/convert/mp3` - Converte mídia para MP3
- `POST /v1/media/transcribe` - Transcreve ou traduz áudio/vídeo
- `POST /v1/media/metadata` - Extrai metadados de arquivos de mídia
- `POST /v1/BETA/media/download` - Baixa mídia de URLs usando yt-dlp

### S3
- `POST /v1/s3/upload` - Faz upload de arquivo para S3

## Resolução de Problemas

### Erro: "API_KEY environment variable is not set"

Configure a variável de ambiente:
```bash
export API_KEY="sua-chave-aqui"
```

### Erro: "Porta já está em uso"

Encontre e pare o processo:
```bash
lsof -ti:8080 | xargs kill
```

Ou use outra porta modificando o código.

### Swagger não mostra endpoints

Certifique-se de que:
1. A API está rodando
2. Você está acessando `/apidocs/` (não `/docs`)
3. Os endpoints têm documentação Swagger nos docstrings

## Notas

- A maioria dos endpoints suporta `webhook_url` para notificações assíncronas
- Endpoints de processamento podem retornar código 202 (enfileirado) ou 200 (processado imediatamente)
- Use `bypass_queue=True` para processamento síncrono quando necessário

