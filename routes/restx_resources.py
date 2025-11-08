# Registro de Resources Flask-RESTX para documentação Swagger
# Este arquivo registra endpoints principais no Flask-RESTX para aparecerem no Swagger

from flask_restx import Namespace, Resource, fields
from flask import request, current_app
from services.authentication import authenticate
from app_utils import queue_task_wrapper
import logging

logger = logging.getLogger(__name__)

# Criar namespaces
toolkit_ns = Namespace('Toolkit', description='Endpoints utilitários da API')
video_ns = Namespace('Video', description='Endpoints para processamento de vídeo')
audio_ns = Namespace('Audio', description='Endpoints para processamento de áudio')
media_ns = Namespace('Media', description='Endpoints para processamento de mídia geral')
s3_ns = Namespace('S3', description='Endpoints para upload S3')

# Modelos de resposta comuns
success_response_model = toolkit_ns.model('SuccessResponse', {
    'code': fields.Integer(example=200),
    'endpoint': fields.String(example='/v1/toolkit/test'),
    'job_id': fields.String(example='a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6'),
    'message': fields.String(example='success'),
    'response': fields.Raw(description='Resposta do endpoint'),
    'build_number': fields.String(example='211')
})

# Modelo de requisição para endpoints POST
media_url_model = media_ns.model('MediaURLRequest', {
    'media_url': fields.String(required=True, description='URL do arquivo de mídia', example='https://example.com/video.mp4'),
    'webhook_url': fields.String(description='URL para receber notificação quando o job for concluído', example='https://example.com/webhook'),
    'id': fields.String(description='ID opcional para rastreamento da requisição', example='custom-request-id')
})

def call_blueprint_function(endpoint_name):
    """Helper para chamar funções de blueprint através do sistema de queue"""
    def wrapper(self):
        # Obter função do blueprint através do endpoint
        view_func = current_app.view_functions.get(endpoint_name)
        if view_func:
            # Chamar através do sistema de queue
            job_id = 'restx-doc'
            data = request.json if request.is_json else {}
            result = view_func(job_id=job_id, data=data)
            if isinstance(result, tuple) and len(result) == 3:
                return result[0], result[2]  # Retornar (data, status_code)
            return result
        return {'error': 'Endpoint not found'}, 404
    return wrapper

# Toolkit - Test
@toolkit_ns.route('/v1/toolkit/test')
@toolkit_ns.doc(security='APIKeyHeader')
class TestAPI(Resource):
    @toolkit_ns.doc(
        description='Testa se a API está funcionando corretamente',
        responses={
            200: 'API funcionando corretamente',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @toolkit_ns.marshal_with(success_response_model, code=200)
    def get(self):
        """Testa se a API está funcionando corretamente"""
        # Aplicar autenticação
        from services.authentication import authenticate
        auth_result = authenticate()(lambda: None)()
        if auth_result and isinstance(auth_result, tuple) and auth_result[1] == 401:
            return {'error': 'Unauthorized'}, 401
        
        # Chamar através do sistema de queue do app
        from flask import current_app
        job_id = 'restx-test'
        data = {}
        result = current_app.queue_task(bypass_queue=True)(lambda: self._call_test(job_id, data))()
        if isinstance(result, tuple) and len(result) == 2:
            return result[0], result[1]
        return result
    
    def _call_test(self, job_id, data):
        from routes.v1.toolkit.test import test_api
        return test_api(job_id, data)

# Media - Convert to MP3
@media_ns.route('/v1/media/convert/mp3')
@media_ns.doc(security='APIKeyHeader')
class ConvertToMP3(Resource):
    @media_ns.doc(
        description='Converte arquivos de mídia para formato MP3',
        body=media_url_model,
        responses={
            200: 'Conversão concluída com sucesso',
            202: 'Requisição enfileirada para processamento',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @media_ns.expect(media_url_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Converte arquivos de mídia para formato MP3"""
        from flask import current_app
        job_id = 'restx-convert-mp3'
        data = request.json or {}
        result = current_app.queue_task(bypass_queue=False)(lambda: self._call_convert_mp3(job_id, data))()
        if isinstance(result, tuple) and len(result) == 2:
            return result[0], result[1]
        return result
    
    def _call_convert_mp3(self, job_id, data):
        from routes.v1.media.convert.media_to_mp3 import convert_media_to_mp3
        return convert_media_to_mp3(job_id, data)

# Media - Transcribe
@media_ns.route('/v1/media/transcribe')
@media_ns.doc(security='APIKeyHeader')
class TranscribeMedia(Resource):
    transcribe_model = media_ns.model('TranscribeRequest', {
        'media_url': fields.String(required=True, description='URL do arquivo de mídia', example='https://example.com/video.mp4'),
        'task': fields.String(enum=['transcribe', 'translate'], description='Tipo de tarefa', example='transcribe'),
        'include_text': fields.Boolean(description='Incluir texto simples na resposta', example=True),
        'include_srt': fields.Boolean(description='Incluir arquivo SRT na resposta', example=False),
        'response_type': fields.String(enum=['direct', 'cloud'], description='Tipo de resposta', example='direct'),
        'webhook_url': fields.String(description='URL para receber notificação', example='https://example.com/webhook'),
        'id': fields.String(description='ID opcional', example='custom-request-id')
    })
    
    @media_ns.doc(
        description='Transcreve ou traduz áudio/vídeo usando Whisper',
        body=transcribe_model,
        responses={
            200: 'Transcrição concluída com sucesso',
            202: 'Requisição enfileirada',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @media_ns.expect(transcribe_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Transcreve ou traduz áudio/vídeo usando Whisper"""
        from flask import current_app
        job_id = 'restx-transcribe'
        data = request.json or {}
        result = current_app.queue_task(bypass_queue=False)(lambda: self._call_transcribe(job_id, data))()
        if isinstance(result, tuple) and len(result) == 2:
            return result[0], result[1]
        return result
    
    def _call_transcribe(self, job_id, data):
        from routes.v1.media.media_transcribe import transcribe
        return transcribe(job_id, data)

# Video - Concatenate
@video_ns.route('/v1/video/concatenate')
@video_ns.doc(security='APIKeyHeader')
class ConcatenateVideos(Resource):
    concatenate_model = video_ns.model('ConcatenateRequest', {
        'video_urls': fields.List(
            fields.Nested(video_ns.model('VideoURL', {
                'video_url': fields.String(required=True, example='https://example.com/video1.mp4')
            })),
            required=True,
            description='Array de URLs dos vídeos a serem concatenados',
            min_items=1
        ),
        'webhook_url': fields.String(description='URL para receber notificação', example='https://example.com/webhook'),
        'id': fields.String(description='ID opcional', example='custom-request-id')
    })
    
    @video_ns.doc(
        description='Concatena múltiplos vídeos em um único arquivo',
        body=concatenate_model,
        responses={
            200: 'Vídeos concatenados com sucesso',
            202: 'Requisição enfileirada',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @video_ns.expect(concatenate_model)
    @video_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Concatena múltiplos vídeos em um único arquivo"""
        from flask import current_app
        job_id = 'restx-concatenate-video'
        data = request.json or {}
        result = current_app.queue_task(bypass_queue=False)(lambda: self._call_concatenate_video(job_id, data))()
        if isinstance(result, tuple) and len(result) == 2:
            return result[0], result[1]
        return result
    
    def _call_concatenate_video(self, job_id, data):
        from routes.v1.video.concatenate import combine_videos
        return combine_videos(job_id, data)

# Audio - Concatenate
@audio_ns.route('/v1/audio/concatenate')
@audio_ns.doc(security='APIKeyHeader')
class ConcatenateAudio(Resource):
    concatenate_model = audio_ns.model('ConcatenateAudioRequest', {
        'audio_urls': fields.List(
            fields.Nested(audio_ns.model('AudioURL', {
                'audio_url': fields.String(required=True, example='https://example.com/audio1.mp3')
            })),
            required=True,
            description='Array de URLs dos arquivos de áudio a serem concatenados',
            min_items=1
        ),
        'webhook_url': fields.String(description='URL para receber notificação', example='https://example.com/webhook'),
        'id': fields.String(description='ID opcional', example='custom-request-id')
    })
    
    @audio_ns.doc(
        description='Concatena múltiplos arquivos de áudio em um único arquivo',
        body=concatenate_model,
        responses={
            200: 'Áudios concatenados com sucesso',
            202: 'Requisição enfileirada',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @audio_ns.expect(concatenate_model)
    @audio_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Concatena múltiplos arquivos de áudio em um único arquivo"""
        from flask import current_app
        job_id = 'restx-concatenate-audio'
        data = request.json or {}
        result = current_app.queue_task(bypass_queue=False)(lambda: self._call_concatenate_audio(job_id, data))()
        if isinstance(result, tuple) and len(result) == 2:
            return result[0], result[1]
        return result
    
    def _call_concatenate_audio(self, job_id, data):
        from routes.v1.audio.concatenate import combine_audio
        return combine_audio(job_id, data)

# S3 - Upload
@s3_ns.route('/v1/s3/upload')
@s3_ns.doc(security='APIKeyHeader')
class S3Upload(Resource):
    upload_model = s3_ns.model('S3UploadRequest', {
        'file_url': fields.String(required=True, description='URL do arquivo para fazer upload', example='https://example.com/file.mp4'),
        'filename': fields.String(description='Nome do arquivo no S3', example='my-file.mp4'),
        'public': fields.Boolean(description='Tornar arquivo público', example=False),
        'webhook_url': fields.String(description='URL para receber notificação', example='https://example.com/webhook'),
        'id': fields.String(description='ID opcional', example='custom-request-id')
    })
    
    @s3_ns.doc(
        description='Faz upload de um arquivo para S3 via streaming direto da URL',
        body=upload_model,
        responses={
            200: 'Upload concluído com sucesso',
            202: 'Requisição enfileirada',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @s3_ns.expect(upload_model)
    @s3_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Faz upload de um arquivo para S3 via streaming direto da URL"""
        from flask import current_app
        job_id = 'restx-s3-upload'
        data = request.json or {}
        result = current_app.queue_task(bypass_queue=False)(lambda: self._call_s3_upload(job_id, data))()
        if isinstance(result, tuple) and len(result) == 2:
            return result[0], result[1]
        return result
    
    def _call_s3_upload(self, job_id, data):
        from routes.v1.s3.upload import s3_upload_endpoint
        return s3_upload_endpoint(job_id, data)

# Função para registrar todos os namespaces na API
def register_restx_namespaces(api):
    """Registra todos os namespaces na API Flask-RESTX"""
    api.add_namespace(toolkit_ns)
    api.add_namespace(video_ns)
    api.add_namespace(audio_ns)
    api.add_namespace(media_ns)
    api.add_namespace(s3_ns)
    
    # Adicionar outros namespaces vazios para completar
    from flask_restx import Namespace as NS
    api.add_namespace(NS('Image', description='Endpoints para processamento de imagens'))
    api.add_namespace(NS('GCP', description='Endpoints para Google Cloud Platform'))
    api.add_namespace(NS('FFmpeg', description='Endpoints para operações FFmpeg avançadas'))
    api.add_namespace(NS('Code', description='Endpoints para execução de código'))

