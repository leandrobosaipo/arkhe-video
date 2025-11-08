# Como Testar o Instagram Downloader

## Correções Realizadas

✅ **Problema da porta ocupada resolvido**: O script agora detecta automaticamente se a porta 8000 está em uso e procura uma porta alternativa (8001, 8002, etc.)

## Passo a Passo para Testar

### 1. Parar processos na porta 8000 (se necessário)

Se você ainda tiver um processo rodando na porta 8000, pare-o primeiro:

```bash
# Encontrar o processo
lsof -ti:8000

# Parar o processo (substitua PID pelo número retornado)
kill -9 PID
```

Ou simplesmente use uma porta diferente:

```bash
PORT=8001 python instagram_downloader.py
```

### 2. Iniciar o servidor

**Opção A: Executar diretamente**
```bash
python instagram_downloader.py
```

**Opção B: Usando uvicorn**
```bash
uvicorn instagram_downloader:app --host 0.0.0.0 --port 8000
```

**Opção C: Porta personalizada**
```bash
PORT=8001 python instagram_downloader.py
```

Você verá uma mensagem como:
```
INFO: Usando porta 8000
INFO: Iniciando servidor em http://0.0.0.0:8000
INFO: Documentação Swagger disponível em http://0.0.0.0:8000/docs
```

### 3. Testar com uma URL do Instagram

#### Método 1: Usando o script de teste (Recomendado)

```bash
python test_instagram_downloader.py "https://www.instagram.com/p/SUA_URL_AQUI/"
```

O script vai:
- Verificar se a API está rodando
- Fazer o download
- Mostrar os detalhes do resultado

#### Método 2: Usando curl (POST)

```bash
curl -X POST "http://localhost:8000/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/SUA_URL_AQUI/"}'
```

#### Método 3: Usando curl (GET)

```bash
curl "http://localhost:8000/download?url=https://www.instagram.com/p/SUA_URL_AQUI/"
```

#### Método 4: Usando a interface Swagger

1. Abra o navegador em: http://localhost:8000/docs
2. Expanda o endpoint `/download`
3. Clique em "Try it out"
4. Cole a URL do Instagram no campo `url`
5. Clique em "Execute"

### 4. Verificar o arquivo baixado

Os arquivos são salvos na pasta `downloads/` com o formato:
```
{titulo_post}_{timestamp_humano}.{extensao}
```

Exemplo:
```
downloads/post_incrivel_2025-01-27_15-30-45.mp4
```

## Exemplo Completo

```bash
# Terminal 1: Iniciar o servidor
python instagram_downloader.py

# Terminal 2: Testar com uma URL
python test_instagram_downloader.py "https://www.instagram.com/p/ABC123xyz/"
```

## Resolução de Problemas

### Erro: "Porta já está em uso"
✅ **Resolvido**: O script agora detecta automaticamente e usa outra porta.

### Erro: "Não foi possível extrair informações"
- Verifique se a URL do Instagram está correta
- Certifique-se de que o post é público
- Alguns posts podem requerer autenticação

### Erro: "Timeout"
- O download pode demorar para posts grandes
- Verifique sua conexão com a internet
- Tente novamente após alguns segundos

### Erro: "Arquivo não foi criado"
- Verifique permissões de escrita na pasta `downloads/`
- Certifique-se de que há espaço em disco suficiente

## Testando com sua URL

Para testar com a URL que você mencionou (sssinstagram.com), você precisa primeiro obter a URL real do post do Instagram. O sssinstagram.com é apenas um serviço de download, não uma URL de post.

**Passos:**
1. Abra o Instagram no navegador ou app
2. Vá até o post que deseja baixar
3. Copie a URL do post (formato: `https://www.instagram.com/p/ABC123/`)
4. Use essa URL no teste:

```bash
python test_instagram_downloader.py "https://www.instagram.com/p/ABC123/"
```

## Verificar Logs

O servidor mostra logs detalhados no terminal. Fique atento a:
- ✅ Mensagens de sucesso
- ⚠️ Avisos sobre portas alternativas
- ❌ Erros de download ou conexão

