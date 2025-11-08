#!/usr/bin/env python3
"""
Script de teste para a API de download do Instagram.

Uso:
    python test_instagram_downloader.py "https://www.instagram.com/p/ABC123/"
"""

import sys
import os
import requests
import json
from typing import Optional

def test_download(url: str, api_url: str = "http://localhost:8000", method: str = "POST"):
    """
    Testa o download de uma URL do Instagram.
    
    Args:
        url: URL do post do Instagram
        api_url: URL base da API (padrão: http://localhost:8000)
        method: Método HTTP a usar ("POST" ou "GET")
    """
    print(f"\n{'='*60}")
    print(f"Testando download do Instagram")
    print(f"{'='*60}")
    print(f"URL do Instagram: {url}")
    print(f"API URL: {api_url}")
    print(f"Método: {method}")
    print(f"{'='*60}\n")
    
    try:
        if method.upper() == "POST":
            endpoint = f"{api_url}/download"
            response = requests.post(
                endpoint,
                json={"url": url},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
        else:
            endpoint = f"{api_url}/download"
            response = requests.get(
                endpoint,
                params={"url": url},
                timeout=60
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Download realizado com sucesso!")
            print(f"\nDetalhes:")
            print(f"  - Sucesso: {data.get('success')}")
            print(f"  - Mensagem: {data.get('message')}")
            print(f"  - Nome do arquivo: {data.get('file_name')}")
            print(f"  - Caminho completo: {data.get('file_path')}")
            print(f"  - Tamanho: {data.get('file_size', 0):,} bytes ({data.get('file_size', 0) / 1024 / 1024:.2f} MB)")
            print(f"  - Tipo de mídia: {data.get('media_type')}")
            return True
        else:
            print(f"❌ Erro na requisição!")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Erro: {error_data.get('detail', 'Erro desconhecido')}")
            except:
                print(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API.")
        print(f"   Certifique-se de que o servidor está rodando em {api_url}")
        print(f"   Execute: python instagram_downloader.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Erro: Timeout na requisição (mais de 60 segundos)")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False


def test_api_health(api_url: str = "http://localhost:8000"):
    """
    Testa se a API está respondendo.
    
    Args:
        api_url: URL base da API
    """
    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API está respondendo!")
            print(f"   Versão: {data.get('version')}")
            print(f"   Docs: {api_url}{data.get('docs')}")
            return True
        else:
            print(f"⚠️  API respondeu com status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ API não está respondendo em {api_url}")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar API: {str(e)}")
        return False


if __name__ == "__main__":
    # Verificar se a API está rodando
    api_url = os.environ.get("API_URL", "http://localhost:8000")
    
    print("Verificando se a API está rodando...")
    if not test_api_health(api_url):
        print(f"\n⚠️  A API não está respondendo. Inicie o servidor com:")
        print(f"   python instagram_downloader.py")
        print(f"   ou")
        print(f"   uvicorn instagram_downloader:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Obter URL do Instagram
    if len(sys.argv) > 1:
        instagram_url = sys.argv[1]
    else:
        print("\n" + "="*60)
        print("Script de teste - Instagram Downloader API")
        print("="*60)
        instagram_url = input("\nDigite a URL do post do Instagram: ").strip()
    
    if not instagram_url:
        print("❌ URL não fornecida!")
        sys.exit(1)
    
    # Validar URL básica
    if not instagram_url.startswith(("http://", "https://")):
        print("❌ URL inválida! Deve começar com http:// ou https://")
        sys.exit(1)
    
    # Testar download
    success = test_download(instagram_url, api_url)
    
    if success:
        print("\n" + "="*60)
        print("✅ Teste concluído com sucesso!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ Teste falhou!")
        print("="*60)
        sys.exit(1)

