#!/usr/bin/env python3
"""
Exemplo de teste para a API Arkhe Video
Demonstra como usar os endpoints principais da API
"""

import requests
import json
import sys

# Configuração
API_KEY = "dev-key-123456"  # Altere para sua chave
BASE_URL = "http://localhost:8080"

def test_toolkit_test():
    """Testa o endpoint básico de teste da API"""
    print("\n=== Teste 1: Toolkit Test ===")
    url = f"{BASE_URL}/v1/toolkit/test"
    headers = {"x-api-key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def test_media_metadata():
    """Testa extração de metadados de mídia"""
    print("\n=== Teste 2: Media Metadata ===")
    url = f"{BASE_URL}/v1/media/metadata"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Use uma URL de exemplo (substitua por uma URL real)
    payload = {
        "media_url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Metadados extraídos:")
            print(f"  - Formato: {data.get('response', {}).get('format', 'N/A')}")
            print(f"  - Duração: {data.get('response', {}).get('duration_formatted', 'N/A')}")
            print(f"  - Resolução: {data.get('response', {}).get('resolution', 'N/A')}")
        else:
            print(f"Resposta: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False

def main():
    print("=" * 50)
    print("Teste da API Arkhe Video")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    
    results = []
    
    # Teste 1: Endpoint básico
    results.append(("Toolkit Test", test_toolkit_test()))
    
    # Teste 2: Metadados (comentado por padrão - requer URL válida)
    # results.append(("Media Metadata", test_media_metadata()))
    
    # Resumo
    print("\n" + "=" * 50)
    print("Resumo dos Testes")
    print("=" * 50)
    for name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{name}: {status}")
    
    print("\n💡 Dica: Acesse http://localhost:8080/apidocs/ para ver todos os endpoints disponíveis!")
    print("💡 Dica: Use o Swagger UI para testar endpoints interativamente!")

if __name__ == "__main__":
    main()

