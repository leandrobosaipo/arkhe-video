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



# routes/media_to_mp3.py
from flask import Blueprint, current_app
from app_utils import *
import logging
from services.v1.media.convert.media_to_mp3 import process_media_to_mp3
from services.authentication import authenticate
from services.cloud_storage import upload_file
import os

v1_media_convert_mp3_bp = Blueprint('v1_media_convert_mp3', __name__)
logger = logging.getLogger(__name__)

@v1_media_convert_mp3_bp.route('/v1/media/convert/mp3', methods=['POST'])
@v1_media_convert_mp3_bp.route('/v1/media/transform/mp3', methods=['POST']) #depleft for backwards compatibility, do not use.
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "bitrate": {"type": "string", "pattern": "^[0-9]+k$"},
        "sample_rate": {"type": "number"}
    },
    "required": ["media_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def convert_media_to_mp3(job_id, data):
    """
    Converte arquivos de mídia para formato MP3
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
              description: URL do arquivo de mídia para conversão
              example: https://example.com/video.mp4
            bitrate:
              type: string
              pattern: "^[0-9]+k$"
              description: Bitrate do áudio em formato Xk (padrão: 128k)
              example: "128k"
            sample_rate:
              type: number
              description: Taxa de amostragem em Hz (opcional)
              example: 44100
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
        description: Conversão concluída com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/media/transform/mp3"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: string
              format: uri
              example: "https://example.com/audio.mp3"
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
    media_url = data['media_url']
    webhook_url = data.get('webhook_url')
    id = data.get('id')
    bitrate = data.get('bitrate', '128k')
    sample_rate = data.get('sample_rate')

    logger.info(f"Job {job_id}: Received media-to-mp3 request for media URL: {media_url}")

    try:
        output_file = process_media_to_mp3(media_url, job_id, bitrate, sample_rate)
        logger.info(f"Job {job_id}: Media conversion process completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Converted media uploaded to cloud storage: {cloud_url}")

        return cloud_url, "/v1/media/transform/mp3", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during media conversion process - {str(e)}")
        return str(e), "/v1/media/transform/mp3", 500