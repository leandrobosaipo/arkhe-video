from flask import Blueprint
from app_utils import *
import logging
from services.v1.audio.concatenate import process_audio_concatenate
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_audio_concatenate_bp = Blueprint("v1_audio_concatenate", __name__)
logger = logging.getLogger(__name__)


@v1_audio_concatenate_bp.route("/v1/audio/concatenate", methods=["POST"])
@authenticate
@validate_payload(
    {
        "type": "object",
        "properties": {
            "audio_urls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"audio_url": {"type": "string", "format": "uri"}},
                    "required": ["audio_url"],
                },
                "minItems": 1,
            },
            "webhook_url": {"type": "string", "format": "uri"},
            "id": {"type": "string"},
        },
        "required": ["audio_urls"],
        "additionalProperties": False,
    }
)
@queue_task_wrapper(bypass_queue=False)
def combine_audio(job_id, data):
    """
    Concatena múltiplos arquivos de áudio em um único arquivo
    ---
    tags:
      - Audio
    security:
      - APIKeyHeader: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: header
        name: x-api-key
        type: string
        required: true
        description: Chave de API para autenticação
        example: sua-chave-api-aqui
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - audio_urls
          properties:
            audio_urls:
              type: array
              description: Array de objetos contendo URLs dos arquivos de áudio a serem concatenados
              minItems: 1
              items:
                type: object
                required:
                  - audio_url
                properties:
                  audio_url:
                    type: string
                    format: uri
                    description: URL do arquivo de áudio
                    example: https://example.com/audio1.mp3
            webhook_url:
              type: string
              format: uri
              description: URL para receber notificação quando o job for concluído
              example: https://example.com/webhook
            id:
              type: string
              description: ID opcional para rastreamento da requisição
              example: custom-request-id
    responses:
      200:
        description: Áudios concatenados com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/audio/concatenate"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: string
              format: uri
              example: "https://example.com/concatenated-audio.mp3"
            build_number:
              type: string
              example: "211"
      202:
        description: Requisição enfileirada para processamento
      400:
        description: Requisição inválida
      401:
        description: Não autorizado - API key inválida ou ausente
      500:
        description: Erro interno do servidor
    """
    media_urls = data["audio_urls"]
    webhook_url = data.get("webhook_url")
    id = data.get("id")

    logger.info(
        f"Job {job_id}: Received combine-audio request for {len(media_urls)} audio files"
    )

    try:
        output_file = process_audio_concatenate(media_urls, job_id)
        logger.info(f"Job {job_id}: Audio combination process completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(
            f"Job {job_id}: Combined audio uploaded to cloud storage: {cloud_url}"
        )

        return cloud_url, "/v1/audio/concatenate", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during audio combination process - {str(e)}")
        return str(e), "/v1/audio/concatenate", 500
