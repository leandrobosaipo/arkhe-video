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
from services.v1.video.split import split_video
from services.authentication import authenticate

v1_video_split_bp = Blueprint('v1_video_split', __name__)
logger = logging.getLogger(__name__)

@v1_video_split_bp.route('/v1/video/split', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "splits": {
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
    "required": ["video_url", "splits"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def video_split(job_id, data):
    """
    Divide um vídeo em múltiplos segmentos
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
            - splits
          properties:
            video_url:
              type: string
              format: uri
              description: URL do arquivo de vídeo a ser dividido
              example: https://example.com/video.mp4
            splits:
              type: array
              description: Array de segmentos para dividir o vídeo
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
        description: Vídeo dividido com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/video/split"
            id:
              type: string
              example: "custom-request-id"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: array
              items:
                type: object
                properties:
                  file_url:
                    type: string
                    format: uri
                    example: "https://example.com/split-1.mp4"
            run_time:
              type: number
              example: 5.234
            total_time:
              type: number
              example: 5.357
            build_number:
              type: string
              example: "211"
      202:
        description: Requisição enfileirada para processamento
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 202
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "processing"
            queue_length:
              type: integer
              example: 2
      400:
        description: Requisição inválida
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 400
            message:
              type: string
              example: "Invalid request payload"
      401:
        description: Não autorizado - API key inválida ou ausente
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 401
            message:
              type: string
              example: "Unauthorized"
      500:
        description: Erro interno do servidor
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 500
            message:
              type: string
              example: "Error during video split process"
    """
    video_url = data['video_url']
    splits = data['splits']
    
    # Extract encoding settings with defaults
    video_codec = data.get('video_codec', 'libx264')
    video_preset = data.get('video_preset', 'medium')
    video_crf = data.get('video_crf', 23)
    audio_codec = data.get('audio_codec', 'aac')
    audio_bitrate = data.get('audio_bitrate', '128k')
    
    logger.info(f"Job {job_id}: Received video split request for {video_url}")
    
    try:
        # Process the video file and get list of output files
        output_files, input_filename = split_video(
            video_url=video_url,
            splits=splits,
            job_id=job_id,
            video_codec=video_codec,
            video_preset=video_preset,
            video_crf=video_crf,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate
        )
        
        # Upload all output files to cloud storage
        from services.cloud_storage import upload_file
        result_files = []
        
        for i, output_file in enumerate(output_files):
            cloud_url = upload_file(output_file)
            result_files.append({
                "file_url": cloud_url,
                "start": splits[i]["start"],
                "end": splits[i]["end"]
            })
            # Remove the local file after upload
            # Em modo local, manter o arquivo de saída para facilitar acesso
            import os
            is_local_mode = os.getenv('LOCAL_STORAGE_MODE', '').lower() == 'true'
            if not is_local_mode:
                try:
                    os.remove(output_file)
                    logger.info(f"Job {job_id}: Uploaded and removed split file {i+1}")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Could not remove split file {output_file}: {str(e)}")
            else:
                logger.info(f"Job {job_id}: Modo local ativo - arquivo mantido em: {output_file}")
        
        # Clean up input file (sempre remover)
        import os
        try:
            os.remove(input_filename)
            logger.info(f"Job {job_id}: Removed input file")
        except Exception as e:
            logger.warning(f"Job {job_id}: Could not remove input file {input_filename}: {str(e)}")
        
        # Prepare the response with only file URLs
        response = [{"file_url": item["file_url"]} for item in result_files]
        
        logger.info(f"Job {job_id}: Video split operation completed successfully")
        return response, "/v1/video/split", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error during video split process - {str(e)}")
        return str(e), "/v1/video/split", 500