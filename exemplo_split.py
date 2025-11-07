#!/usr/bin/env python3
"""Exemplo de como dividir um vídeo em duas partes iguais usando a API"""
import requests
import json
import time

# Configurações
API_URL = "http://localhost:8080"
API_KEY = "test_key_123"
VIDEO_URL = "http://localhost:8000/homem-mexendo-celular-varanda.mp4"

# Duração do vídeo: 9.8 segundos
# Dividindo em duas partes iguais:
# - Primeira parte: 00:00:00.000 até 00:00:04.900
# - Segunda parte: 00:00:04.900 até 00:00:09.800

def format_time(seconds):
    """Converte segundos para formato hh:mm:ss.ms"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{int(secs):02d}.{int((secs % 1) * 1000):03d}"

def split_video_in_half():
    """Divide o vídeo em duas partes iguais"""
    
    # Duração total: 9.8 segundos
    duration = 9.8
    half_duration = duration / 2
    
    # Criar os splits
    splits = [
        {
            "start": format_time(0),
            "end": format_time(half_duration)
        },
        {
            "start": format_time(half_duration),
            "end": format_time(duration)
        }
    ]
    
    # Payload da requisição
    payload = {
        "video_url": VIDEO_URL,
        "splits": splits,
        "id": "exemplo-split-duas-partes"
    }
    
    print("=" * 60)
    print("Dividindo vídeo em duas partes iguais")
    print("=" * 60)
    print(f"Vídeo: {VIDEO_URL}")
    print(f"Duração total: {duration} segundos")
    print(f"\nParte 1: {splits[0]['start']} até {splits[0]['end']}")
    print(f"Parte 2: {splits[1]['start']} até {splits[1]['end']}")
    print("\nEnviando requisição...")
    
    # Fazer a requisição
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/v1/video/split",
            headers=headers,
            json=payload,
            timeout=300  # 5 minutos de timeout
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 202:
            # Requisição foi enfileirada
            job_id = response.json().get("job_id")
            print(f"\n⚠️  Requisição enfileirada. Job ID: {job_id}")
            print("Use o endpoint /v1/toolkit/job/status para verificar o status")
            
        elif response.status_code == 200:
            # Sucesso
            result = response.json()
            files = result.get("response", [])
            print(f"\n✅ Sucesso! Vídeo dividido em {len(files)} partes:")
            for i, file_info in enumerate(files, 1):
                print(f"  Parte {i}: {file_info.get('file_url', 'N/A')}")
        
        return response.json()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
        print("Certifique-se de que o servidor Flask está rodando na porta 8080")
        return None
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        return None

if __name__ == "__main__":
    split_video_in_half()

