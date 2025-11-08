# Sistema híbrido para registrar blueprints Flask no Flask-RESTX
# Permite manter os blueprints existentes e adicionar documentação Swagger automaticamente

from flask_restx import Namespace, Resource
from flask import current_app
import inspect

def register_blueprints_to_restx(api, app):
    """
    Cria namespaces básicos no Flask-RESTX para documentação Swagger
    Os endpoints continuam funcionando através dos blueprints Flask
    """
    # Criar namespaces para cada categoria
    namespaces_config = {
        'Video': 'Endpoints para processamento de vídeo',
        'Audio': 'Endpoints para processamento de áudio',
        'Media': 'Endpoints para processamento de mídia geral',
        'Image': 'Endpoints para processamento de imagens',
        'Toolkit': 'Endpoints utilitários da API',
        'S3': 'Endpoints para upload S3',
        'GCP': 'Endpoints para Google Cloud Platform',
        'FFmpeg': 'Endpoints para operações FFmpeg avançadas',
        'Code': 'Endpoints para execução de código',
    }
    
    # Criar e registrar namespaces
    for name, description in namespaces_config.items():
        ns = Namespace(name, description=description)
        api.add_namespace(ns)
    
    # Nota: Os endpoints reais continuam funcionando através dos blueprints Flask
    # Flask-RESTX apenas fornece a documentação Swagger
    # Para adicionar documentação detalhada, crie Resources específicos nos namespaces
    
    return api

