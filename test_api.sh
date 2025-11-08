#!/bin/bash

# Script de teste para a API Arkhe Video
# Uso: ./test_api.sh [API_KEY] [BASE_URL]

API_KEY=${1:-"123456"}
BASE_URL=${2:-"http://localhost:8080"}

echo "=== Testando API Arkhe Video ==="
echo "API Key: $API_KEY"
echo "Base URL: $BASE_URL"
echo ""

# Teste 1: Verificar se a API está rodando
echo "1. Testando endpoint /v1/toolkit/test..."
response=$(curl -s -w "\n%{http_code}" -H "x-api-key: $API_KEY" "$BASE_URL/v1/toolkit/test")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" == "200" ]; then
    echo "✅ API está funcionando!"
    echo "Resposta: $body"
else
    echo "❌ Erro: HTTP $http_code"
    echo "Resposta: $body"
fi

echo ""
echo "=== Acesse a documentação Swagger em: $BASE_URL/apidocs/ ==="

