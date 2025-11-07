# Variáveis de Ambiente - Exemplo

Copie este arquivo para `.env` e configure com seus valores reais.

```bash
# API Configuration
API_KEY=sua-chave-api-aqui

# Storage Configuration
# Pasta padrão para armazenamento local de arquivos temporários
LOCAL_STORAGE_PATH=/tmp

# DigitalOcean Spaces Configuration (Recomendado)
# Para usar DigitalOcean Spaces, você precisa de:
# 1. Criar um Space no painel da DigitalOcean
# 2. Gerar Access Keys (API -> Spaces Keys)
# 3. Configurar as variáveis abaixo

# Endpoint do DigitalOcean Spaces (formato: https://seu-bucket.regiao.digitaloceanspaces.com)
S3_ENDPOINT_URL=https://seu-bucket.nyc3.digitaloceanspaces.com

# Access Key do DigitalOcean Spaces
S3_ACCESS_KEY=sua-access-key-aqui

# Secret Key do DigitalOcean Spaces
S3_SECRET_KEY=sua-secret-key-aqui

# Bucket name (opcional - pode ser extraído automaticamente da URL se não fornecido)
S3_BUCKET_NAME=seu-bucket-name

# Região (opcional - pode ser extraída automaticamente da URL se não fornecido)
# Exemplos: nyc3, sgp1, ams3, sfo3, etc.
S3_REGION=nyc3

# Google Cloud Platform Configuration (Alternativa)
# Descomente e configure se preferir usar GCP Storage ao invés de DigitalOcean Spaces
# GCP_BUCKET_NAME=seu-bucket-gcp
# GCP_SA_CREDENTIALS={"type":"service_account","project_id":"..."}

# Performance Tuning (Opcional)
# Limite máximo de tarefas na fila (0 = ilimitado)
MAX_QUEUE_LENGTH=0

# Número de workers do Gunicorn (padrão: CPU cores + 1)
GUNICORN_WORKERS=4

# Timeout do Gunicorn em segundos (aumente para arquivos grandes)
GUNICORN_TIMEOUT=300

# Modo Local para Testes (Apenas para desenvolvimento)
# LOCAL_STORAGE_MODE=true
# LOCAL_STORAGE_BASE_URL=http://localhost:8000
# LOCAL_SERVE_DIR=/caminho/para/diretorio
```

## Como Obter Credenciais do DigitalOcean Spaces

1. Acesse o [Painel da DigitalOcean](https://cloud.digitalocean.com/)
2. Vá em **Spaces** no menu lateral
3. Crie um novo Space ou selecione um existente
4. Vá em **Settings** > **Spaces Keys**
5. Clique em **Generate New Key**
6. Copie a **Access Key** e **Secret Key**
7. Use o endpoint do Space no formato: `https://seu-bucket.regiao.digitaloceanspaces.com`

## Variáveis Obrigatórias

- `API_KEY`: Chave de API para autenticação (obrigatória)
- `S3_ENDPOINT_URL`: Endpoint do DigitalOcean Spaces (obrigatória se usar Spaces)
- `S3_ACCESS_KEY`: Access Key do DigitalOcean Spaces (obrigatória se usar Spaces)
- `S3_SECRET_KEY`: Secret Key do DigitalOcean Spaces (obrigatória se usar Spaces)

## Variáveis Opcionais

- `S3_BUCKET_NAME`: Nome do bucket (extraído automaticamente da URL se não fornecido)
- `S3_REGION`: Região do Space (extraída automaticamente da URL se não fornecido)
- `LOCAL_STORAGE_PATH`: Pasta para arquivos temporários (padrão: `/tmp`)
- `MAX_QUEUE_LENGTH`: Limite de tarefas na fila (padrão: 0 = ilimitado)
- `GUNICORN_WORKERS`: Número de workers (padrão: CPU cores + 1)
- `GUNICORN_TIMEOUT`: Timeout em segundos (padrão: 30)

