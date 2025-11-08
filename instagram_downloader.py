#!/usr/bin/env python3
"""
API FastAPI para download de vídeos e fotos do Instagram.

Este script permite baixar conteúdo do Instagram através de uma API REST simples
com documentação Swagger automática.

Uso:
    python instagram_downloader.py
    
    ou
    
    uvicorn instagram_downloader:app --host 0.0.0.0 --port 8000

Acesse a documentação Swagger em: http://localhost:8000/docs
"""

import os
import re
import yt_dlp
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl, Field
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Instagram Downloader API",
    description="API para download de vídeos e fotos do Instagram",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Diretório padrão para downloads
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)


class DownloadRequest(BaseModel):
    """Modelo de requisição para download"""
    url: HttpUrl = Field(..., description="URL do post do Instagram")
    download_dir: Optional[str] = Field(
        None,
        description="Diretório para salvar o arquivo (padrão: downloads/)"
    )


class DownloadResponse(BaseModel):
    """Modelo de resposta do download"""
    success: bool
    message: str
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    media_type: Optional[str] = None


def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres inválidos do nome do arquivo.
    
    Args:
        filename: Nome do arquivo original
        
    Returns:
        Nome do arquivo sanitizado
    """
    # Remove caracteres especiais e espaços
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    # Limita o tamanho do nome
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def get_human_timestamp() -> str:
    """
    Retorna timestamp em formato humano legível.
    
    Returns:
        String com timestamp no formato YYYY-MM-DD_HH-MM-SS
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def extract_media_info(url: str) -> dict:
    """
    Extrai informações da mídia do Instagram usando yt-dlp.
    
    Args:
        url: URL do post do Instagram
        
    Returns:
        Dicionário com informações da mídia
        
    Raises:
        Exception: Se não conseguir extrair informações
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        logger.error(f"Erro ao extrair informações: {str(e)}")
        raise


def download_instagram_media(url: str, download_dir: Optional[str] = None) -> dict:
    """
    Baixa mídia do Instagram e salva no diretório especificado.
    
    Args:
        url: URL do post do Instagram
        download_dir: Diretório para salvar (padrão: downloads/)
        
    Returns:
        Dicionário com informações do download
        
    Raises:
        HTTPException: Se ocorrer erro no download
    """
    # Determinar diretório de download
    if download_dir is None:
        download_dir = DEFAULT_DOWNLOAD_DIR
    else:
        download_dir = os.path.abspath(download_dir)
        os.makedirs(download_dir, exist_ok=True)
    
    # Extrair informações da mídia
    try:
        info = extract_media_info(url)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Não foi possível extrair informações da URL: {str(e)}"
        )
    
    # Obter título ou usar padrão
    title = info.get('title', 'instagram_post')
    if not title or title == 'NA':
        title = 'instagram_post'
    
    # Sanitizar título
    title = sanitize_filename(title)
    
    # Criar nome do arquivo com timestamp
    timestamp = get_human_timestamp()
    ext = info.get('ext', 'mp4')
    filename = f"{title}_{timestamp}.{ext}"
    filepath = os.path.join(download_dir, filename)
    
    # Configurar yt-dlp para download
    ydl_opts = {
        'outtmpl': filepath,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        # Fazer o download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Verificar se o arquivo foi criado
        if not os.path.exists(filepath):
            # Tentar encontrar o arquivo com extensão diferente
            base_path = os.path.splitext(filepath)[0]
            for possible_ext in ['mp4', 'jpg', 'png', 'webp', 'mov']:
                possible_path = f"{base_path}.{possible_ext}"
                if os.path.exists(possible_path):
                    filepath = possible_path
                    filename = os.path.basename(filepath)
                    break
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Arquivo não foi criado após o download"
                )
        
        # Obter tamanho do arquivo
        file_size = os.path.getsize(filepath)
        
        # Determinar tipo de mídia
        media_type = 'video' if info.get('ext') in ['mp4', 'mov', 'webm'] else 'image'
        
        return {
            'success': True,
            'message': 'Download concluído com sucesso',
            'file_path': filepath,
            'file_name': filename,
            'file_size': file_size,
            'media_type': media_type
        }
        
    except Exception as e:
        logger.error(f"Erro durante o download: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao baixar mídia: {str(e)}"
        )


@app.get("/", tags=["Info"])
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "Instagram Downloader API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoint": "/download"
    }


@app.post("/download", response_model=DownloadResponse, tags=["Download"])
async def download_post(request: DownloadRequest):
    """
    Baixa vídeo ou foto do Instagram.
    
    Recebe a URL de um post do Instagram e faz o download do conteúdo,
    salvando na pasta downloads/ (ou pasta especificada) com nome
    relacionado ao post e timestamp humano.
    
    **Exemplo de uso:**
    ```json
    {
        "url": "https://www.instagram.com/p/ABC123/",
        "download_dir": "downloads"
    }
    ```
    
    **Parâmetros:**
    - `url`: URL completa do post do Instagram (obrigatório)
    - `download_dir`: Diretório para salvar (opcional, padrão: downloads/)
    
    **Retorna:**
    - Informações sobre o download realizado
    """
    try:
        result = download_instagram_media(str(request.url), request.download_dir)
        return DownloadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado: {str(e)}"
        )


@app.get("/download", response_model=DownloadResponse, tags=["Download"])
async def download_post_get(url: str = Query(..., description="URL do post do Instagram")):
    """
    Baixa vídeo ou foto do Instagram (método GET).
    
    Versão alternativa usando método GET para facilitar testes.
    
    **Exemplo:**
    ```
    GET /download?url=https://www.instagram.com/p/ABC123/
    ```
    """
    try:
        result = download_instagram_media(url)
        return DownloadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado: {str(e)}"
        )


def find_free_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """
    Encontra uma porta livre começando da porta especificada.
    
    Args:
        start_port: Porta inicial para tentar
        max_attempts: Número máximo de tentativas
        
    Returns:
        Número da porta livre encontrada
    """
    import socket
    
    for i in range(max_attempts):
        port = start_port + i
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"Não foi possível encontrar uma porta livre após {max_attempts} tentativas")


if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Tentar obter porta do ambiente ou usar padrão
    default_port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Verificar se a porta está disponível
    try:
        port = default_port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.close()
        logger.info(f"Usando porta {port}")
    except OSError:
        logger.warning(f"Porta {default_port} está em uso, procurando porta alternativa...")
        port = find_free_port(default_port)
        logger.info(f"Porta alternativa encontrada: {port}")
    
    logger.info(f"Iniciando servidor em http://{host}:{port}")
    logger.info(f"Documentação Swagger disponível em http://{host}:{port}/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=True
    )

