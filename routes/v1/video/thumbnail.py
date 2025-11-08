# Copyright (c) 2025 Stephen G. Pope
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.



from flask import Blueprint, jsonify
from app_utils import *
import logging
from services.v1.video.thumbnail import extract_thumbnail
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_video_thumbnail_bp = Blueprint('v1_video_thumbnail', __name__)
logger = logging.getLogger(__name__)

@v1_video_thumbnail_bp.route('/v1/video/thumbnail', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "second": {"type": "number", "minimum": 0},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def generate_thumbnail(job_id, data):
    """
    Extrai uma thumbnail de um vídeo em um timestamp específico
    ---
    tags:
      - Video
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
            - video_url
          properties:
            video_url:
              type: string
              format: uri
              description: URL do arquivo de vídeo
              example: https://example.com/video.mp4
            second:
              type: number
              description: Segundo do vídeo para extrair a thumbnail (padrão: 0)
              minimum: 0
              example: 10.5
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
        description: Thumbnail extraída com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/video/thumbnail"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: string
              format: uri
              example: "https://example.com/thumbnail.jpg"
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
    video_url = data.get('video_url')
    second = data.get('second', 0)  # Default to 0 if not provided
    webhook_url = data.get('webhook_url')

    logger.info(f"Job {job_id}: Received thumbnail extraction request for {video_url} at {second} seconds")

    try:
        # Process thumbnail extraction
        thumbnail_path = extract_thumbnail(video_url, job_id, second)

        # Upload the thumbnail to cloud storage
        file_url = upload_file(thumbnail_path)

        logger.info(f"Job {job_id}: Thumbnail uploaded to cloud storage at {file_url}")

        # Return the URL of the uploaded thumbnail
        return file_url, "/v1/video/thumbnail", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error during thumbnail extraction - {str(e)}")
        return str(e), "/v1/video/thumbnail", 500
