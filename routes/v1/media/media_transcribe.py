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
import os
import json
from services.v1.media.media_transcribe import process_transcribe_media
from services.authentication import authenticate
from services.cloud_storage import upload_file

v1_media_transcribe_bp = Blueprint('v1_media_transcribe', __name__)
logger = logging.getLogger(__name__)

@v1_media_transcribe_bp.route('/v1/media/transcribe', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "media_url": {"type": "string", "format": "uri"},
        "task": {"type": "string", "enum": ["transcribe", "translate"]},
        "include_text": {"type": "boolean"},
        "include_srt": {"type": "boolean"},
        "include_segments": {"type": "boolean"},
        "word_timestamps": {"type": "boolean"},
        "response_type": {"type": "string", "enum": ["direct", "cloud"]},
        "language": {"type": "string"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "words_per_line": {"type": "integer", "minimum": 1}
    },
    "required": ["media_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def transcribe(job_id, data):
    """
    Transcreve ou traduz áudio/vídeo usando Whisper
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
              description: URL do arquivo de mídia para transcrição
              example: https://example.com/video.mp4
            task:
              type: string
              enum: [transcribe, translate]
              description: Tipo de tarefa - transcrever ou traduzir (padrão: transcribe)
              example: transcribe
            include_text:
              type: boolean
              description: Incluir texto simples na resposta (padrão: true)
              example: true
            include_srt:
              type: boolean
              description: Incluir arquivo SRT na resposta (padrão: false)
              example: false
            include_segments:
              type: boolean
              description: Incluir segmentos com timestamps (padrão: false)
              example: false
            word_timestamps:
              type: boolean
              description: Incluir timestamps por palavra (padrão: false)
              example: false
            response_type:
              type: string
              enum: [direct, cloud]
              description: Tipo de resposta - direta ou URLs de cloud storage (padrão: direct)
              example: direct
            language:
              type: string
              description: Código de idioma para transcrição (opcional, auto-detect se não especificado)
              example: pt
            words_per_line:
              type: integer
              description: Número máximo de palavras por linha no SRT (mínimo: 1)
              minimum: 1
              example: 8
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
        description: Transcrição concluída com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/transcribe/media"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: object
              properties:
                text:
                  type: string
                  description: Texto transcrito (se include_text=true e response_type=direct)
                srt:
                  type: string
                  description: Conteúdo SRT (se include_srt=true e response_type=direct)
                segments:
                  type: array
                  description: Segmentos com timestamps (se include_segments=true e response_type=direct)
                text_url:
                  type: string
                  format: uri
                  description: URL do arquivo de texto (se response_type=cloud)
                srt_url:
                  type: string
                  format: uri
                  description: URL do arquivo SRT (se response_type=cloud)
                segments_url:
                  type: string
                  format: uri
                  description: URL do arquivo de segmentos (se response_type=cloud)
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
    task = data.get('task', 'transcribe')
    include_text = data.get('include_text', True)
    include_srt = data.get('include_srt', False)
    include_segments = data.get('include_segments', False)
    word_timestamps = data.get('word_timestamps', False)
    response_type = data.get('response_type', 'direct')
    language = data.get('language', None)
    webhook_url = data.get('webhook_url')
    id = data.get('id')
    words_per_line = data.get('words_per_line', None)

    logger.info(f"Job {job_id}: [01] Recebendo requisição de transcrição | URL: {media_url} | Task: {task}")

    try:
        logger.info(f"Job {job_id}: [02] Parâmetros validados | Include: text={include_text}, srt={include_srt}, segments={include_segments}")
        
        result = process_transcribe_media(media_url, task, include_text, include_srt, include_segments, word_timestamps, response_type, language, job_id, words_per_line)
        logger.info(f"Job {job_id}: [11] Processamento concluído com sucesso")

        if response_type == "direct":
            # Extrair valores do resultado
            text_value = result[0] if result[0] is not None else None
            srt_value = result[1] if result[1] is not None else None
            segments_value = result[2] if result[2] is not None else None
            
            # Proteção dupla: converter bytes para string
            if text_value is not None:
                if isinstance(text_value, bytes):
                    logger.warning(f"Job {job_id}: [09] Convertendo bytes para string | Campo: text")
                    text_value = text_value.decode('utf-8', errors='ignore')
                else:
                    text_value = str(text_value)
            
            if srt_value is not None:
                if isinstance(srt_value, bytes):
                    logger.warning(f"Job {job_id}: [09] Convertendo bytes para string | Campo: srt")
                    srt_value = srt_value.decode('utf-8', errors='ignore')
                else:
                    srt_value = str(srt_value)
            
            # Validar segments antes de incluir
            if segments_value is not None:
                if not isinstance(segments_value, list):
                    logger.warning(f"Job {job_id}: [09] Segments não é lista, convertendo | Tipo: {type(segments_value)}")
                    segments_value = None
                else:
                    # Tentar validar serialização de segments
                    try:
                        json.dumps(segments_value)
                        logger.info(f"Job {job_id}: [09] Segments validado | Total: {len(segments_value)} segmentos")
                    except (TypeError, ValueError) as e:
                        logger.error(f"Job {job_id}: [09] Segments não serializável, limpando novamente | Erro: {str(e)}")
                        # Re-limpar se necessário (chamada recursiva de limpeza)
                        from services.v1.media.media_transcribe import clean_segments_for_json
                        segments_value = clean_segments_for_json(
                            [s for s in segments_value if isinstance(s, dict)], 
                            word_timestamps
                        ) if segments_value else None
            
            result_json = {
                "text": text_value,
                "srt": srt_value,
                "segments": segments_value,
                "text_url": None,
                "srt_url": None,
                "segments_url": None,
            }
            
            # Validação final de serialização
            logger.info(f"Job {job_id}: [10] Testando serialização JSON")
            try:
                json.dumps(result_json)
                logger.info(f"Job {job_id}: [10] Serialização OK | Retornando resposta completa")
            except (TypeError, ValueError) as e:
                logger.error(f"Job {job_id}: [FALLBACK] Serialização falhou | Erro: {type(e).__name__}: {str(e)}")
                # Fallback: remover segments e tentar novamente
                result_json_fallback = {
                    "text": text_value,
                    "srt": srt_value,
                    "segments": None,
                    "text_url": None,
                    "srt_url": None,
                    "segments_url": None,
                    "warning": "Segments removidos devido a erro de serialização"
                }
                try:
                    json.dumps(result_json_fallback)
                    logger.warning(f"Job {job_id}: [FALLBACK] Retornando resposta parcial (sem segments)")
                    result_json = result_json_fallback
                except Exception as e2:
                    logger.error(f"Job {job_id}: [ERRO] Fallback também falhou | Erro: {str(e2)}")
                    raise ValueError(f"Erro crítico de serialização: {str(e2)}")
            
            logger.info(f"Job {job_id}: [11] Retornando resposta | Tipo: direct | Campos: text={text_value is not None}, srt={srt_value is not None}, segments={segments_value is not None}")
            return result_json, "/v1/transcribe/media", 200

        else:
            logger.info(f"Job {job_id}: [11] Processando resposta cloud | Upload de arquivos")
            
            cloud_urls = {
                "text": None,
                "srt": None,
                "segments": None,
                "text_url": upload_file(result[0]) if include_text is True and result[0] else None,
                "srt_url": upload_file(result[1]) if include_srt is True and result[1] else None,
                "segments_url": upload_file(result[2]) if include_segments is True and result[2] else None,
            }
            
            # Validação de serialização para cloud também
            try:
                json.dumps(cloud_urls)
                logger.info(f"Job {job_id}: [10] Serialização cloud OK")
            except (TypeError, ValueError) as e:
                logger.error(f"Job {job_id}: [ERRO] Cloud URLs não serializáveis | Erro: {str(e)}")
                raise

            if include_text is True and result[0]:
                os.remove(result[0])
            if include_srt is True and result[1]:
                os.remove(result[1])
            if include_segments is True and result[2]:
                os.remove(result[2])
            
            logger.info(f"Job {job_id}: [11] Retornando resposta | Tipo: cloud | URLs: text={cloud_urls['text_url'] is not None}, srt={cloud_urls['srt_url'] is not None}, segments={cloud_urls['segments_url'] is not None}")
            return cloud_urls, "/v1/transcribe/media", 200

    except Exception as e:
        logger.error(f"Job {job_id}: [ERRO] Falha na transcrição | Erro: {type(e).__name__}: {str(e)}")
        return str(e), "/v1/transcribe/media", 500
