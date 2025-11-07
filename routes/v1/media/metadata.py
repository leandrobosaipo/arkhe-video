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



from flask import Blueprint, request, jsonify
from app_utils import validate_payload, queue_task_wrapper
import logging
from services.v1.media.metadata import get_media_metadata
from services.authentication import authenticate

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
v1_media_metadata_bp = Blueprint('v1_media_metadata', __name__)

@v1_media_metadata_bp.route('/v1/media/metadata', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=True)  # Set to execute immediately instead of queueing
def media_metadata(job_id, data):
    """
    Extrai metadados de um arquivo de mídia
    ---
    tags:
      - Media
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
            - media_url
          properties:
            media_url:
              type: string
              format: uri
              description: URL do arquivo de mídia para análise
              example: https://example.com/video.mp4
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
        description: Metadados extraídos com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/media/metadata"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: object
              properties:
                filesize:
                  type: integer
                  example: 15679283
                filesize_mb:
                  type: number
                  example: 14.95
                duration:
                  type: number
                  example: 87.46
                duration_formatted:
                  type: string
                  example: "00:01:27.46"
                format:
                  type: string
                  example: "mp4"
                has_video:
                  type: boolean
                  example: true
                video_codec:
                  type: string
                  example: "h264"
                width:
                  type: integer
                  example: 1920
                height:
                  type: integer
                  example: 1080
                resolution:
                  type: string
                  example: "1920x1080"
                fps:
                  type: number
                  example: 30.0
                has_audio:
                  type: boolean
                  example: true
                audio_codec:
                  type: string
                  example: "aac"
                audio_channels:
                  type: integer
                  example: 2
                audio_sample_rate:
                  type: integer
                  example: 48000
            build_number:
              type: string
              example: "211"
      400:
        description: Requisição inválida
      401:
        description: Não autorizado
      500:
        description: Erro interno do servidor
    """
    media_url = data['media_url']
    logger.info(f"Job {job_id}: Received metadata request for {media_url}")
    
    try:
        # Extract metadata from the media file
        metadata = get_media_metadata(media_url, job_id)
        logger.info(f"Job {job_id}: Successfully extracted metadata")
        
        # Return the metadata directly
        return metadata, "/v1/media/metadata", 200
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Job {job_id}: Error extracting metadata - {error_message}")
        return error_message, "/v1/media/metadata", 500