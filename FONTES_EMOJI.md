# Guia de Instalação e Uso de Fontes de Emoji

Este guia explica como instalar e usar fontes de emoji no endpoint `/v1/ffmpeg/compose` para renderizar emojis em vídeos.

## Visão Geral

O endpoint `/v1/ffmpeg/compose` suporta renderização de emojis através de dois métodos:

1. **Filtro `drawtext`**: Suporta emojis, mas renderiza em escala de cinza/monocromático (não colorido)
2. **Filtro `subtitles`**: Suporta emojis coloridos quando usado com arquivos ASS (Advanced SubStation Alpha)

## Formato de Fonte

- **Formato necessário**: TTF (TrueType Font)
- **Fonte recomendada**: Noto Color Emoji
- **macOS**: Apple Color Emoji (já vem no sistema, mas pode ter limitações com FFmpeg)
- **Linux/Docker**: Noto Color Emoji (recomendado)

## Instalação no macOS (Desenvolvimento Local)

### Método 1: Usando Font Book (Recomendado)

1. **Baixar a fonte Noto Color Emoji:**
   - Visite: https://github.com/googlefonts/noto-emoji/releases
   - Baixe o arquivo `NotoColorEmoji.ttf` da versão mais recente
   - Ou use o link direto: https://github.com/googlefonts/noto-emoji/blob/main/fonts/NotoColorEmoji.ttf

2. **Instalar a fonte:**
   - Abra o arquivo `NotoColorEmoji.ttf` (duplo clique)
   - Clique em "Instalar Fonte" no Font Book
   - A fonte será instalada em `~/Library/Fonts/`

### Método 2: Via Linha de Comando

```bash
# Criar diretório de fontes se não existir
mkdir -p ~/Library/Fonts

# Baixar a fonte
curl -L -o ~/Library/Fonts/NotoColorEmoji.ttf \
  https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf

# Atualizar cache de fontes (se necessário)
fc-cache -fv
```

### Verificar Instalação

Para verificar se a fonte foi instalada corretamente:

```bash
# Listar fontes disponíveis
fc-list | grep -i "noto.*emoji\|emoji"

# Ou verificar diretamente
ls ~/Library/Fonts/NotoColorEmoji.ttf
```

## Docker/EasyPanel

A fonte **Noto Color Emoji já está instalada** no Dockerfile (linha 13: `fonts-noto-color-emoji`). Não é necessária nenhuma ação adicional.

**Localização da fonte no container:**
- `/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf`

## Uso no Endpoint `/v1/ffmpeg/compose`

### Exemplo 1: Usando drawtext com Emoji (Monocromático)

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/video.mp4"
    }
  ],
  "filters": [
    {
      "filter": "drawtext=text='Olá 😎 Mundo':fontfile=/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf:fontsize=48:x=100:y=100:fontcolor=white"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "copy"}
      ]
    }
  ],
  "webhook_url": "https://example.com/webhook",
  "id": "emoji-example-1"
}
```

**Nota para macOS local:**
- Use o caminho completo da fonte instalada, por exemplo:
  - `fontfile=/Users/seu-usuario/Library/Fonts/NotoColorEmoji.ttf`
  - Ou use `fontfile=/System/Library/Fonts/Supplemental/Apple Color Emoji.ttc` (Apple Color Emoji)

### Exemplo 2: Usando subtitles com ASS para Emojis Coloridos

Para emojis coloridos, você precisa criar um arquivo ASS e hospedá-lo em uma URL pública.

1. **Criar arquivo ASS com emoji:**

```ass
[Script Info]
Title: Emoji Colorido
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Color Emoji,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,Olá 😎 Mundo!
```

2. **Fazer upload do arquivo ASS** para um servidor público (S3, GCS, etc.)

3. **Usar no compose:**

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/video.mp4"
    }
  ],
  "filters": [
    {
      "filter": "subtitles='https://example.com/legendas.ass'"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "copy"}
      ]
    }
  ],
  "webhook_url": "https://example.com/webhook",
  "id": "emoji-colorido-example"
}
```

## Limitações e Considerações

### drawtext Filter
- ✅ Suporta emojis
- ❌ **Não renderiza emojis coloridos** (apenas monocromático/escala de cinza)
- ✅ Funciona com qualquer fonte de emoji instalada

### subtitles Filter (libass)
- ✅ Suporta emojis coloridos
- ✅ Renderização completa de cores
- ⚠️ Requer arquivo ASS hospedado em URL pública
- ✅ Usa libass que tem suporte completo a fontes coloridas

## Resolução de Problemas

### Fonte não encontrada no macOS

Se o FFmpeg não encontrar a fonte:

1. Verifique se a fonte está instalada:
   ```bash
   fc-list | grep -i emoji
   ```

2. Use o caminho completo no filtro:
   ```json
   "filter": "drawtext=text='Test':fontfile=/Users/seu-usuario/Library/Fonts/NotoColorEmoji.ttf:fontsize=48"
   ```

3. Atualize o cache de fontes:
   ```bash
   fc-cache -fv
   ```

### Emojis não aparecem no vídeo

1. Verifique se a fonte está especificada corretamente no filtro
2. Certifique-se de que o caminho da fonte está correto
3. Para Docker, use: `/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf`
4. Teste com um emoji simples primeiro (ex: 😀)

### Emojis aparecem em preto e branco

Isso é esperado quando usando o filtro `drawtext`. Para emojis coloridos, use o filtro `subtitles` com arquivo ASS.

## Recursos Adicionais

- [Documentação do endpoint FFmpeg Compose](docs/ffmpeg/ffmpeg_compose.md)
- [Noto Emoji GitHub Repository](https://github.com/googlefonts/noto-emoji)
- [FFmpeg drawtext Documentation](https://ffmpeg.org/ffmpeg-filters.html#drawtext)
- [ASS Subtitle Format Specification](https://github.com/libass/libass/wiki/ASS-Subtitle-Format)

## Exemplos Completos

### Exemplo Completo: Vídeo com Texto e Emoji

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/video.mp4"
    }
  ],
  "filters": [
    {
      "filter": "drawtext=text='Bem-vindo! 🎉':fontfile=/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf:fontsize=60:x=(w-text_w)/2:y=100:fontcolor=white:borderw=2:bordercolor=black"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-preset", "argument": "medium"},
        {"option": "-crf", "argument": "23"},
        {"option": "-c:a", "argument": "copy"}
      ]
    }
  ],
  "webhook_url": "https://example.com/webhook",
  "id": "video-com-emoji"
}
```

Este exemplo adiciona texto centralizado com emoji no topo do vídeo, com borda preta para melhor legibilidade.
