# Exemplo de endpoint convertido para Flask-RESTX
# Este arquivo mostra como converter endpoints existentes para usar Flask-RESTX

from flask_restx import Namespace, Resource, fields
from flask import request
from services.authentication import authenticate
from services.cloud_storage import upload_file
from app_utils import queue_task_wrapper
from config import LOCAL_STORAGE_PATH
import os
import logging

logger = logging.getLogger(__name__)

# Criar namespace para Toolkit
toolkit_ns = Namespace('Toolkit', description='Endpoints utilitários da API')

# Definir modelos de resposta
success_response = toolkit_ns.model('SuccessResponse', {
    'code': fields.Integer(example=200),
    'endpoint': fields.String(example='/v1/toolkit/test'),
    'job_id': fields.String(example='a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6'),
    'message': fields.String(example='success'),
    'response': fields.String(example='https://example.com/success.txt'),
    'build_number': fields.String(example='211')
})

@toolkit_ns.route('/v1/toolkit/test')
@toolkit_ns.doc(security='APIKeyHeader')
class TestAPI(Resource):
    @toolkit_ns.doc(
        description='Testa se a API está funcionando corretamente',
        responses={
            200: 'API funcionando corretamente',
            401: 'Não autorizado - API key inválida ou ausente',
            500: 'Erro interno do servidor'
        }
    )
    @toolkit_ns.marshal_with(success_response, code=200)
    @authenticate
    @queue_task_wrapper(bypass_queue=True)
    def get(self, job_id, data):
        """Testa se a API está funcionando corretamente"""
        logger.info(f"Job {job_id}: Testing NCA Toolkit API setup")
        
        try:
            # Create test file
            test_filename = os.path.join(LOCAL_STORAGE_PATH, "success.txt")
            with open(test_filename, 'w') as f:
                f.write("You have successfully installed the NCA Toolkit API, great job!")
            
            # Upload file to cloud storage
            upload_url = upload_file(test_filename)
            
            # Clean up local file
            os.remove(test_filename)
            
            return {
                'code': 200,
                'endpoint': '/v1/toolkit/test',
                'job_id': job_id,
                'message': 'success',
                'response': upload_url,
                'build_number': '211'
            }, 200
            
        except Exception as e:
            logger.error(f"Job {job_id}: Error testing API setup - {str(e)}")
            return {'error': str(e)}, 500

# Função para registrar o namespace (chamada de app.py após criar a API)
def register_toolkit_namespace(api):
    """Registra o namespace Toolkit na API Flask-RESTX"""
    api.add_namespace(toolkit_ns)

