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



from flask import Blueprint
from app_utils import *
import logging
from services.v1.video.cut import cut_media
from services.authentication import authenticate

v1_video_cut_bp = Blueprint('v1_video_cut', __name__)
logger = logging.getLogger(__name__)

@v1_video_cut_bp.route('/v1/video/cut', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "cuts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "string"},
                    "end": {"type": "string"}
                },
                "required": ["start", "end"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "video_codec": {"type": "string"},
        "video_preset": {"type": "string"},
        "video_crf": {"type": "number", "minimum": 0, "maximum": 51},
        "audio_codec": {"type": "string"},
        "audio_bitrate": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url", "cuts"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def video_cut(job_id, data):
    """
    Remove segmentos especificados de um arquivo de vídeo
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
            - cuts
          properties:
            video_url:
              type: string
              format: uri
              description: URL do arquivo de vídeo
              example: https://example.com/video.mp4
            cuts:
              type: array
              description: Array de segmentos a serem removidos do vídeo
              minItems: 1
              items:
                type: object
                required:
                  - start
                  - end
                properties:
                  start:
                    type: string
                    description: Tempo de início no formato hh:mm:ss.ms
                    example: "00:00:10.000"
                  end:
                    type: string
                    description: Tempo de fim no formato hh:mm:ss.ms
                    example: "00:00:20.000"
            video_codec:
              type: string
              description: Codec de vídeo para encoding (padrão: libx264)
              example: libx264
            video_preset:
              type: string
              description: Preset de encoding
              example: medium
            video_crf:
              type: integer
              description: Constant Rate Factor para qualidade (0-51)
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
        description: Vídeo processado com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/video/cut"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: string
              format: uri
              example: "https://example.com/processed-video.mp4"
            build_number:
              type: string
              example: "211"
      202:
        description: Requisição enfileirada
      400:
        description: Requisição inválida
      401:
        description: Não autorizado
      500:
        description: Erro interno do servidor
    """
    video_url = data['video_url']
    cuts = data['cuts']
    
    # Extract encoding settings with defaults
    video_codec = data.get('video_codec', 'libx264')
    video_preset = data.get('video_preset', 'medium')
    video_crf = data.get('video_crf', 23)
    audio_codec = data.get('audio_codec', 'aac')
    audio_bitrate = data.get('audio_bitrate', '128k')
    
    logger.info(f"Job {job_id}: Received video cut request for {video_url}")
    
    try:
        # Process the video file and get local file paths
        output_filename, input_filename = cut_media(
            video_url=video_url,
            cuts=cuts,
            job_id=job_id,
            video_codec=video_codec,
            video_preset=video_preset,
            video_crf=video_crf,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate
        )
        
        # Upload the processed file to cloud storage
        from services.cloud_storage import upload_file
        cloud_url = upload_file(output_filename)
        logger.info(f"Job {job_id}: Uploaded output to cloud: {cloud_url}")
        
        # Clean up temporary files
        import os
        os.remove(input_filename)
        os.remove(output_filename)
        logger.info(f"Job {job_id}: Removed temporary files")
        
        logger.info(f"Job {job_id}: Video cut operation completed successfully")
        return cloud_url, "/v1/video/cut", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error during video cut process - {str(e)}")
        return str(e), "/v1/video/cut", 500