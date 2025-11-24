#!/usr/bin/env python3
"""
Teste específico para validar correção de bytes em text
"""

import requests
import json
import sys

API_KEY = "dev-key-123456"
BASE_URL = "http://localhost:8080"

def test_text_only():
    """Teste com apenas text (caso que estava falhando)"""
    print("\n=== Teste: Apenas text (include_segments=false) ===")
    url = f"{BASE_URL}/v1/media/transcribe"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Payload similar ao que falhou no servidor
    payload = {
        "media_url": "https://cod5.nyc3.digitaloceanspaces.com/upload/reframe/2025/11/24/f95899208501492eb5e39bb241232585.mp4",
        "include_text": True,
        "include_srt": False,
        "include_segments": False,
        "response_type": "direct",
        "language": "pt"
    }
    
    try:
        print(f"Enviando requisição para: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Tentar serializar novamente para garantir que é JSON válido
            json_str = json.dumps(data)
            print(f"✅ Sucesso! Resposta JSON válida ({len(json_str)} bytes)")
            print(f"   Text transcrito: {data.get('response', {}).get('text', '')[:100]}...")
            return True
        elif response.status_code == 202:
            print("✅ Requisição enfileirada (202)")
            print(f"   Job ID: {data.get('job_id')}")
            return True
        else:
            print(f"❌ Erro: {response.text[:500]}")
            return False
    except json.JSONDecodeError as e:
        print(f"❌ Erro de serialização JSON: {e}")
        print(f"   Resposta: {response.text[:500]}")
        return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Teste de Correção: Bytes em text")
    print("=" * 60)
    success = test_text_only()
    sys.exit(0 if success else 1)

