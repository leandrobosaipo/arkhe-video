#!/usr/bin/env python3
"""
Teste específico para o vídeo fornecido
Testa o endpoint /v1/media/transcribe com o vídeo real que estava causando erro
"""

import requests
import json
import sys

API_KEY = "dev-key-123456"
BASE_URL = "http://localhost:8080"
VIDEO_URL = "https://cod5.nyc3.digitaloceanspaces.com/upload/reframe/2025/11/24/f95899208501492eb5e39bb241232585.mp4"

def test_transcribe():
    """Teste com apenas text (caso que estava falhando)"""
    print("\n" + "=" * 60)
    print("Teste: Transcrição do Vídeo Específico")
    print("=" * 60)
    print(f"URL do vídeo: {VIDEO_URL}")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    
    url = f"{BASE_URL}/v1/media/transcribe"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Payload similar ao que falhou no servidor
    payload = {
        "media_url": VIDEO_URL,
        "include_text": True,
        "include_srt": False,
        "include_segments": False,
        "response_type": "direct",
        "language": "pt"
    }
    
    try:
        print(f"\n📤 Enviando requisição para: {url}")
        print(f"📋 Payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        response = requests.post(url, headers=headers, json=payload, timeout=300)
        print(f"\n📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                # Tentar serializar novamente para garantir que é JSON válido
                json_str = json.dumps(data)
                print(f"✅ Sucesso! Resposta JSON válida ({len(json_str)} bytes)")
                
                # Mostrar informações da resposta
                if 'response' in data and data['response']:
                    response_data = data['response']
                    if 'text' in response_data:
                        text_preview = response_data['text'][:200] if response_data['text'] else ""
                        print(f"📝 Texto transcrito (primeiros 200 chars): {text_preview}...")
                        print(f"📏 Tamanho total do texto: {len(response_data.get('text', ''))} caracteres")
                
                print(f"\n📊 Resposta completa:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Erro de serialização JSON: {e}")
                print(f"   Resposta recebida: {response.text[:500]}")
                return False
                
        elif response.status_code == 202:
            try:
                data = response.json()
                print("✅ Requisição enfileirada (202)")
                print(f"   Job ID: {data.get('job_id')}")
                print(f"   Mensagem: {data.get('message')}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao parsear resposta 202: {e}")
                return False
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"   Resposta: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: A requisição demorou mais de 5 minutos")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição: {e}")
        return False
    except Exception as e:
        print(f"❌ Exceção inesperada: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Teste do Endpoint /v1/media/transcribe")
    print("Vídeo: f95899208501492eb5e39bb241232585.mp4")
    print("=" * 60)
    
    success = test_transcribe()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TESTE PASSOU")
        print("=" * 60)
        return 0
    else:
        print("❌ TESTE FALHOU")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

