# Exemplo: Dividir Vídeo em Duas Partes Iguais

Este exemplo demonstra como usar a API para dividir um vídeo em duas partes iguais.

## Pré-requisitos

1. Python 3.11+
2. FFmpeg instalado
3. Dependências do projeto instaladas (`pip install -r requirements.txt`)

## Configuração

### 1. Iniciar o servidor HTTP para servir arquivos locais

Em um terminal, execute:

```bash
python3 -m http.server 8000 --directory /Users/leandrobosaipo/Downloads
```

### 2. Iniciar o servidor Flask

Em outro terminal, execute:

```bash
cd /Users/leandrobosaipo/Sites/scripts/arkhe-video

export API_KEY=test_key_123
export LOCAL_STORAGE_PATH=/tmp
export LOCAL_STORAGE_MODE=true
export LOCAL_STORAGE_BASE_URL=http://localhost:8000
export LOCAL_SERVE_DIR=/Users/leandrobosaipo/Downloads

python3 app.py
```

## Exemplo de Uso

### Obter duração do vídeo

Primeiro, você precisa saber a duração do vídeo. Você pode usar `ffprobe`:

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 video.mp4
```

### Dividir o vídeo

Execute o script de exemplo:

```bash
python3 exemplo_split.py
```

Ou faça uma requisição manual usando `curl`:

```bash
curl -X POST http://localhost:8080/v1/video/split \
  -H "x-api-key: test_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "http://localhost:8000/homem-mexendo-celular-varanda.mp4",
    "splits": [
      {
        "start": "00:00:00.000",
        "end": "00:00:04.900"
      },
      {
        "start": "00:00:04.900",
        "end": "00:00:09.800"
      }
    ],
    "id": "exemplo-split-duas-partes"
  }'
```

## Resposta da API

```json
{
  "code": 200,
  "endpoint": "/v1/video/split",
  "id": "exemplo-split-duas-partes",
  "job_id": "95761e7f-d5a8-4fe6-a118-2ecd6d879ceb",
  "message": "success",
  "response": [
    {
      "file_url": "http://localhost:8000/95761e7f-d5a8-4fe6-a118-2ecd6d879ceb_split_1.mp4"
    },
    {
      "file_url": "http://localhost:8000/95761e7f-d5a8-4fe6-a118-2ecd6d879ceb_split_2.mp4"
    }
  ],
  "run_time": 1.061,
  "total_time": 1.061
}
```

## Cálculo Automático da Divisão

O script `exemplo_split.py` calcula automaticamente os pontos de divisão:

```python
# Duração total: 9.8 segundos
duration = 9.8
half_duration = duration / 2

# Primeira parte: 00:00:00.000 até 00:00:04.900
# Segunda parte: 00:00:04.900 até 00:00:09.800
```

## Parâmetros Opcionais

Você pode personalizar a codificação do vídeo:

```json
{
  "video_url": "http://localhost:8000/video.mp4",
  "splits": [...],
  "video_codec": "libx264",
  "video_preset": "medium",
  "video_crf": 23,
  "audio_codec": "aac",
  "audio_bitrate": "128k"
}
```

## Notas

- O formato de tempo é `hh:mm:ss.ms` (horas:minutos:segundos.milissegundos)
- Os arquivos processados são salvos no diretório configurado em `LOCAL_SERVE_DIR`
- Para produção, configure GCP ou S3 storage removendo `LOCAL_STORAGE_MODE=true`

