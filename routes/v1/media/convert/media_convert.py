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
from app_utils import validate_payload, queue_task_wrapper
import logging
from services.v1.media.convert.media_convert import process_media_convert
from services.authentication import authenticate
from services.cloud_storage import upload_file
import os

v1_media_convert_bp = Blueprint('v1_media_convert', __name__)
logger = logging.getLogger(__name__)

@v1_media_convert_bp.route('/v1/media/convert', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "format": {"type": "string"},
        "video_codec": {"type": "string"},
        "video_preset": {"type": "string"},
        "video_crf": {"type": "number", "minimum": 0, "maximum": 51},
        "audio_codec": {"type": "string"},
        "audio_bitrate": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["media_url", "format"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def convert_media_format(job_id, data):
    """
    Converte arquivos de mídia entre diferentes formatos
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
            - format
          properties:
            media_url:
              type: string
              format: uri
              description: URL do arquivo de mídia para conversão
              example: https://example.com/video.mp4
            format:
              type: string
              description: Formato de saída desejado (ex: mp4, avi, mov, webm)
              example: mp4
            video_codec:
              type: string
              description: Codec de vídeo para encoding (padrão: libx264)
              example: libx264
            video_preset:
              type: string
              description: Preset de encoding (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
              example: medium
            video_crf:
              type: integer
              description: Constant Rate Factor para qualidade (0-51, menor = melhor qualidade)
              minimum: 0
              maximum: 51
              example: 23
            audio_codec:
              type: string
              description: Codec de áudio para encoding (padrão: aac)
              example: aac
            audio_bitrate:
              type: string
              description: Bitrate de áudio
              example: "128k"
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
              example: "/v1/media/convert"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: string
              format: uri
              example: "https://example.com/converted-video.mp4"
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
    output_format = data['format']
    video_codec = data.get('video_codec', 'libx264')
    video_preset = data.get('video_preset', 'medium')
    video_crf = data.get('video_crf', 23)
    audio_codec = data.get('audio_codec', 'aac')
    audio_bitrate = data.get('audio_bitrate', '128k')
    webhook_url = data.get('webhook_url')
    id = data.get('id')

    logger.info(f"Job {job_id}: Received media conversion request for media URL: {media_url} to format: {output_format}")

    try:
        output_file = process_media_convert(
            media_url, 
            job_id, 
            output_format, 
            video_codec, 
            video_preset,
            video_crf,
            audio_codec,
            audio_bitrate,
            webhook_url
        )
        logger.info(f"Job {job_id}: Media format conversion completed successfully")

        cloud_url = upload_file(output_file)
        logger.info(f"Job {job_id}: Converted media uploaded to cloud storage: {cloud_url}")
        
        return cloud_url, "/v1/media/convert", 200

    except Exception as e:
        logger.error(f"Job {job_id}: Error during media conversion process - {str(e)}")
        return {"error": str(e)}, "/v1/media/convert", 500 