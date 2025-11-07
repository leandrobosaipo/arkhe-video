# Guia de Deploy no EasyPanel

Este guia explica como fazer o deploy da Arkhe Video API no EasyPanel.

## Pré-requisitos

- Conta no EasyPanel
- Conta no DigitalOcean Spaces (recomendado) ou GCP Storage
- Credenciais de acesso ao storage configuradas

## Passo 1: Criar Novo App no EasyPanel

1. Acesse seu painel EasyPanel
2. Clique em **"New App"** ou **"Create App"**
3. Selecione **"Docker"** como tipo de aplicação
4. Escolha um nome para sua aplicação (ex: `arkhe-video-api`)

## Passo 2: Configurar Repositório

1. No campo **"Repository"**, insira:
   ```
   https://github.com/leandrobosaipo/arkhe-video.git
   ```
2. Selecione a branch **`main`** (ou a branch desejada)
3. Configure o **"Build Command"** (se necessário):
   ```bash
   docker build -t arkhe-video .
   ```

## Passo 3: Configurar Dockerfile

O EasyPanel deve detectar automaticamente o `Dockerfile` existente no repositório. Se necessário, verifique se o Dockerfile está configurado corretamente.

## Passo 4: Configurar Variáveis de Ambiente

No EasyPanel, vá para a seção **"Environment Variables"** e adicione as seguintes variáveis:

### Variáveis Obrigatórias

```bash
API_KEY=sua-chave-api-aqui
LOCAL_STORAGE_PATH=/tmp
```

### Variáveis para DigitalOcean Spaces (Recomendado)

```bash
S3_ENDPOINT_URL=https://seu-bucket.nyc3.digitaloceanspaces.com
S3_ACCESS_KEY=sua-access-key-aqui
S3_SECRET_KEY=sua-secret-key-aqui
S3_BUCKET_NAME=seu-bucket-name
S3_REGION=nyc3
```

**Nota:** `S3_BUCKET_NAME` e `S3_REGION` são opcionais se você usar o formato completo da URL do endpoint do DigitalOcean Spaces (o sistema extrai automaticamente).

### Variáveis Opcionais (Performance)

```bash
MAX_QUEUE_LENGTH=10
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=300
```

## Passo 5: Configurar Porta

1. Na seção **"Ports"** ou **"Network"**, configure:
   - **Porta Interna**: `8080`
   - **Porta Externa**: Deixe o EasyPanel atribuir automaticamente ou configure uma porta específica

## Passo 6: Configurar Recursos

Recomendações de recursos:

- **CPU**: Mínimo 1 core (2+ cores recomendado para melhor performance)
- **RAM**: Mínimo 2GB (4GB+ recomendado para processamento de vídeo)
- **Disco**: Mínimo 10GB (mais espaço conforme necessário para arquivos temporários)

## Passo 7: Deploy

1. Revise todas as configurações
2. Clique em **"Deploy"** ou **"Save & Deploy"**
3. Aguarde o build e deploy completarem
4. Verifique os logs para garantir que não há erros

## Passo 8: Verificar Deploy

Após o deploy, teste a API:

1. Acesse a URL fornecida pelo EasyPanel
2. Teste o endpoint de saúde:
   ```bash
   curl -H "x-api-key: sua-chave-api" https://sua-url.easypanel.app/v1/toolkit/test
   ```
3. Acesse a documentação Swagger:
   ```
   https://sua-url.easypanel.app/apidocs/
   ```

## Troubleshooting

### Erro: "No cloud storage settings provided"

Certifique-se de que todas as variáveis do DigitalOcean Spaces estão configuradas corretamente.

### Erro: "API_KEY environment variable is not set"

Verifique se a variável `API_KEY` está configurada nas variáveis de ambiente do EasyPanel.

### Timeout em requisições longas

Para requisições que podem demorar mais de 1 minuto, use o parâmetro `webhook_url` nas requisições da API para receber notificações assíncronas.

### Problemas de memória

Se você estiver processando arquivos grandes, aumente a RAM alocada no EasyPanel e ajuste `GUNICORN_TIMEOUT` para um valor maior (ex: 600 segundos).

## Atualizações

Para atualizar a aplicação:

1. Faça push das alterações para o repositório GitHub
2. No EasyPanel, clique em **"Redeploy"** ou **"Rebuild"**
3. Aguarde o novo deploy completar

## Monitoramento

O EasyPanel fornece logs em tempo real. Monitore os logs para:
- Verificar erros
- Acompanhar o processamento de jobs
- Verificar uso de recursos

## Suporte

Para mais informações sobre a API, consulte:
- [README.md](README.md)
- [ENV_EXAMPLE.md](ENV_EXAMPLE.md)
- Documentação Swagger em `/apidocs/`

