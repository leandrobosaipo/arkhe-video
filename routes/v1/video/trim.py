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
from services.v1.video.trim import trim_video
from services.authentication import authenticate

v1_video_trim_bp = Blueprint('v1_video_trim', __name__)
logger = logging.getLogger(__name__)

@v1_video_trim_bp.route('/v1/video/trim', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "start": {"type": "string"},
        "end": {"type": "string"},
        "video_codec": {"type": "string"},
        "video_preset": {"type": "string"},
        "video_crf": {"type": "number", "minimum": 0, "maximum": 51},
        "audio_codec": {"type": "string"},
        "audio_bitrate": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def video_trim(job_id, data):
    """
    Corta um vídeo removendo partes do início e/ou fim
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
            start:
              type: string
              description: Tempo de início para manter (formato hh:mm:ss.ms). Se não especificado, mantém desde o início
              example: "00:00:10.000"
            end:
              type: string
              description: Tempo de fim para manter (formato hh:mm:ss.ms). Se não especificado, mantém até o fim
              example: "00:01:30.000"
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
        description: Vídeo cortado com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/video/trim"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: string
              format: uri
              example: "https://example.com/trimmed-video.mp4"
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
    start = data.get('start')
    end = data.get('end')
    
    # Extract encoding settings with defaults
    video_codec = data.get('video_codec', 'libx264')
    video_preset = data.get('video_preset', 'medium')
    video_crf = data.get('video_crf', 23)
    audio_codec = data.get('audio_codec', 'aac')
    audio_bitrate = data.get('audio_bitrate', '128k')
    
    logger.info(f"Job {job_id}: Received video trim request for {video_url}")
    
    try:
        # Process the video file and get local file paths
        output_filename, input_filename = trim_video(
            video_url=video_url,
            start=start,
            end=end,
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
        # Sempre remover arquivo de entrada
        try:
            os.remove(input_filename)
            logger.info(f"Job {job_id}: Removed input file: {input_filename}")
        except Exception as e:
            logger.warning(f"Job {job_id}: Could not remove input file {input_filename}: {str(e)}")
        
        # Em modo local, manter o arquivo de saída para facilitar acesso
        is_local_mode = os.getenv('LOCAL_STORAGE_MODE', '').lower() == 'true'
        if not is_local_mode:
            try:
                os.remove(output_filename)
                logger.info(f"Job {job_id}: Cleaned up local output file: {output_filename}")
            except Exception as e:
                logger.warning(f"Job {job_id}: Could not remove output file {output_filename}: {str(e)}")
        else:
            logger.info(f"Job {job_id}: Modo local ativo - arquivo mantido em: {output_filename}")
        
        logger.info(f"Job {job_id}: Video trim operation completed successfully")
        return cloud_url, "/v1/video/trim", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error during video trim process - {str(e)}")
        return str(e), "/v1/video/trim", 500