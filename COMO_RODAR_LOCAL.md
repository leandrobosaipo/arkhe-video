# Como Rodar e Testar Localmente

Este guia explica como executar e testar a API Arkhe Video localmente.

## Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- FFmpeg (será instalado via Docker ou você pode instalar manualmente)

## Passo 1: Instalar Dependências

```bash
pip3 install -r requirements.txt
```

## Passo 2: Configurar Variáveis de Ambiente

Para desenvolvimento local, você precisa configurar as seguintes variáveis:

```bash
export API_KEY="dev-key-123456"
export LOCAL_STORAGE_PATH="/tmp"
export LOCAL_STORAGE_MODE="true"
export LOCAL_STORAGE_BASE_URL="http://localhost:8000"
export LOCAL_SERVE_DIR="/tmp"
```

Ou crie um arquivo `.env` na raiz do projeto com:

```env
API_KEY=dev-key-123456
LOCAL_STORAGE_PATH=/tmp
LOCAL_STORAGE_MODE=true
LOCAL_STORAGE_BASE_URL=http://localhost:8000
LOCAL_SERVE_DIR=/tmp
```

**Nota:** 
- Para desenvolvimento local, não é necessário configurar S3 ou GCP
- O modo `LOCAL_STORAGE_MODE=true` permite usar armazenamento local sem cloud storage
- Os arquivos serão salvos temporariamente em `LOCAL_STORAGE_PATH` ou `LOCAL_SERVE_DIR`

## Passo 3: Rodar a API

### Opção 1: Python Direto (Desenvolvimento)

```bash
python3 app.py
```

A API estará disponível em `http://localhost:8080`

### Opção 2: Gunicorn (Produção/Teste)

```bash
gunicorn -c gunicorn.conf.py app:app
```

## Passo 4: Verificar se Está Funcionando

### Acessar a Documentação Swagger

Abra seu navegador e acesse:
- **Swagger UI**: http://localhost:8080/apidocs/
- **OpenAPI Spec**: http://localhost:8080/apispec.json

### Testar com curl

```bash
curl -H "x-api-key: dev-key-123456" http://localhost:8080/v1/toolkit/test
```

### Usar o Script de Teste

```bash
chmod +x test_api.sh
./test_api.sh dev-key-123456 http://localhost:8080
```

## Exemplos de Testes

### 1. Teste Básico da API

```bash
curl -H "x-api-key: dev-key-123456" \
  http://localhost:8080/v1/toolkit/test
```

### 2. Verificar Status de um Job

```bash
curl -X POST "http://localhost:8080/v1/toolkit/job/status" \
  -H "x-api-key: dev-key-123456" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "seu-job-id-aqui"
  }'
```

### 3. Extrair Metadados de Mídia

```bash
curl -X POST "http://localhost:8080/v1/media/metadata" \
  -H "x-api-key: dev-key-123456" \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://example.com/video.mp4"
  }'
```

## Resolução de Problemas

### Erro: "API_KEY environment variable is not set"

Configure a variável de ambiente:
```bash
export API_KEY="dev-key-123456"
```

### Erro: "No cloud storage settings provided"

Para desenvolvimento local, você precisa ativar o modo de armazenamento local:
```bash
export LOCAL_STORAGE_MODE="true"
export LOCAL_STORAGE_BASE_URL="http://localhost:8000"
export LOCAL_SERVE_DIR="/tmp"
```

### Erro: Porta 8080 já está em uso

Encontre e pare o processo:
```bash
lsof -ti:8080 | xargs kill
```

Ou use outra porta modificando `app.py`:
```python
app.run(host='0.0.0.0', port=8081)  # Mude para 8081
```

### Erro: Módulo não encontrado

Instale as dependências:
```bash
pip3 install -r requirements.txt
```

### FFmpeg não encontrado

Se você estiver rodando sem Docker, instale o FFmpeg:

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Rodar com Docker (Alternativa)

Se preferir usar Docker:

```bash
# Build da imagem
docker build -t arkhe-video .

# Rodar o container
docker run -d -p 8080:8080 \
  -e API_KEY=dev-key-123456 \
  -e LOCAL_STORAGE_PATH=/tmp \
  arkhe-video
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

## Notas Importantes

- A maioria dos endpoints suporta `webhook_url` para notificações assíncronas
- Endpoints de processamento podem retornar código 202 (enfileirado) ou 200 (processado imediatamente)
- Use `bypass_queue=True` para processamento síncrono quando necessário
- Para desenvolvimento local, os arquivos são salvos temporariamente em `/tmp` (ou o caminho configurado em `LOCAL_STORAGE_PATH`)

