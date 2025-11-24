#!/usr/bin/env python3
"""
Teste para o endpoint /v1/media/transcribe
Testa diferentes combinações de parâmetros para garantir que a correção JSON funciona
"""

import requests
import json
import sys

API_KEY = "dev-key-123456"
BASE_URL = "http://localhost:8080"

def test_transcribe_basic():
    """Teste básico sem include_segments"""
    print("\n=== Teste 1: Transcrição Básica (sem segments) ===")
    url = f"{BASE_URL}/v1/media/transcribe"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "media_url": "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
        "include_text": True,
        "include_srt": False,
        "include_segments": False,
        "response_type": "direct"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso! Texto transcrito: {data.get('response', {}).get('text', '')[:100]}...")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def test_transcribe_with_segments():
    """Teste com include_segments=True (caso que estava quebrando)"""
    print("\n=== Teste 2: Transcrição com Segments (correção JSON) ===")
    url = f"{BASE_URL}/v1/media/transcribe"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "media_url": "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
        "include_text": True,
        "include_srt": False,
        "include_segments": True,
        "response_type": "direct"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            segments = data.get('response', {}).get('segments', [])
            print(f"✅ Sucesso! Segmentos retornados: {len(segments)}")
            if segments:
                print(f"   Primeiro segmento: {json.dumps(segments[0], indent=2)[:200]}...")
            # Validar que é JSON serializável
            json_str = json.dumps(data)
            print(f"✅ JSON serializável: {len(json_str)} bytes")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
    except json.JSONDecodeError as e:
        print(f"❌ Erro de serialização JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def test_transcribe_with_word_timestamps():
    """Teste com word_timestamps=True"""
    print("\n=== Teste 3: Transcrição com Word Timestamps ===")
    url = f"{BASE_URL}/v1/media/transcribe"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "media_url": "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
        "include_text": True,
        "include_srt": False,
        "include_segments": True,
        "word_timestamps": True,
        "response_type": "direct"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            segments = data.get('response', {}).get('segments', [])
            print(f"✅ Sucesso! Segmentos com word timestamps: {len(segments)}")
            if segments and 'words' in segments[0]:
                print(f"   Words no primeiro segmento: {len(segments[0]['words'])}")
            # Validar JSON
            json_str = json.dumps(data)
            print(f"✅ JSON serializável: {len(json_str)} bytes")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def main():
    print("=" * 60)
    print("Teste do Endpoint /v1/media/transcribe")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    
    results = []
    
    # Teste 1: Básico
    results.append(("Transcrição Básica", test_transcribe_basic()))
    
    # Teste 2: Com segments (correção principal)
    results.append(("Transcrição com Segments", test_transcribe_with_segments()))
    
    # Teste 3: Com word timestamps
    results.append(("Transcrição com Word Timestamps", test_transcribe_with_word_timestamps()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("Resumo dos Testes")
    print("=" * 60)
    all_passed = True
    for name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n✅ Todos os testes passaram! Correção JSON funcionando.")
        return 0
    else:
        print("\n❌ Alguns testes falharam.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

