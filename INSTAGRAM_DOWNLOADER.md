# Instagram Downloader API

API FastAPI para download de vídeos e fotos do Instagram.

## Instalação

Instale as dependências necessárias:

```bash
pip install -r requirements.txt
```

## Como abrir e editar o arquivo

### Usando VS Code / Cursor:
```bash
code instagram_downloader.py
```

### Usando vim/nano:
```bash
vim instagram_downloader.py
# ou
nano instagram_downloader.py
```

## Como rodar

### Método 1: Executar diretamente
```bash
python instagram_downloader.py
```

### Método 2: Usando uvicorn (recomendado para produção)
```bash
uvicorn instagram_downloader:app --host 0.0.0.0 --port 8000
```

### Método 3: Com variáveis de ambiente
```bash
PORT=8000 HOST=0.0.0.0 python instagram_downloader.py
```

## Acessar a documentação Swagger

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Uso da API

### Endpoint POST /download

```bash
curl -X POST "http://localhost:8000/download" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/p/ABC123/",
    "download_dir": "downloads"
  }'
```

### Endpoint GET /download (alternativo)

```bash
curl "http://localhost:8000/download?url=https://www.instagram.com/p/ABC123/"
```

## Resposta da API

```json
{
  "success": true,
  "message": "Download concluído com sucesso",
  "file_path": "/caminho/completo/arquivo.mp4",
  "file_name": "post_instagram_2025-01-27_14-30-45.mp4",
  "file_size": 1234567,
  "media_type": "video"
}
```

## Estrutura de arquivos

- `instagram_downloader.py` - Script principal da API
- `downloads/` - Pasta padrão onde os arquivos são salvos
- Arquivos são nomeados com: `{titulo_post}_{timestamp}.{extensao}`

## Deploy no Easypanel

Para fazer deploy no Easypanel:

1. Certifique-se de que o arquivo `instagram_downloader.py` está no repositório
2. Configure o serviço no Easypanel:
   - **Tipo**: Web Service
   - **Comando**: `uvicorn instagram_downloader:app --host 0.0.0.0 --port 8000`
   - **Porta**: 8000
   - **Variáveis de ambiente**: (opcional) `PORT`, `HOST`

3. A documentação Swagger estará disponível em `https://seu-dominio.com/docs`

## Limitações

- Posts privados não podem ser baixados sem autenticação
- Posts com múltiplas mídias podem baixar apenas a primeira
- Requer conexão com internet para acessar o Instagram

## Exemplo de uso com Python

```python
import requests

url = "http://localhost:8000/download"
data = {
    "url": "https://www.instagram.com/p/ABC123/"
}

response = requests.post(url, json=data)
print(response.json())
```

