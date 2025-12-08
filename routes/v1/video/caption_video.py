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
from app_utils import validate_payload, queue_task_wrapper, log_job_status
import logging
from services.ass_toolkit import generate_ass_captions_v1
from services.authentication import authenticate
from services.cloud_storage import upload_file
import os
import requests  # Ensure requests is imported for webhook handling
import time
from urllib.parse import urlparse

v1_video_caption_bp = Blueprint('v1_video/caption', __name__)
logger = logging.getLogger(__name__)

def get_humanized_error_message(exception, context=None):
    """
    Mapeia erros técnicos em mensagens humanizadas e amigáveis.
    
    Args:
        exception: A exceção ou string de erro
        context: Dicionário com contexto adicional (video_url, stage, etc.)
    
    Returns:
        Dicionário com mensagem humanizada, tipo, código e sugestões
    """
    error_str = str(exception) if not isinstance(exception, str) else exception
    context = context or {}
    
    # Mapeamento de erros comuns
    error_mappings = {
        "FileNotFoundError": {
            "message": "O arquivo de vídeo não foi encontrado.",
            "type": "FILE_NOT_FOUND",
            "code": "VIDEO_FILE_NOT_FOUND",
            "suggestion": "Verifique se a URL do vídeo está correta e acessível."
        },
        "ConnectionError": {
            "message": "Não foi possível baixar o vídeo.",
            "type": "CONNECTION_ERROR",
            "code": "VIDEO_DOWNLOAD_FAILED",
            "suggestion": "Verifique sua conexão com a internet e se a URL está acessível."
        },
        "Timeout": {
            "message": "A operação demorou muito tempo e foi cancelada.",
            "type": "TIMEOUT_ERROR",
            "code": "OPERATION_TIMEOUT",
            "suggestion": "Tente novamente ou use um arquivo menor."
        },
        "FFmpeg": {
            "message": "Erro ao processar o vídeo com FFmpeg.",
            "type": "FFMPEG_ERROR",
            "code": "VIDEO_PROCESSING_FAILED",
            "suggestion": "Verifique se o formato do arquivo de vídeo é suportado (MP4, AVI, MOV, etc.)."
        },
        "font": {
            "message": "A fonte especificada não está disponível.",
            "type": "FONT_ERROR",
            "code": "FONT_NOT_AVAILABLE",
            "suggestion": "Use uma das fontes disponíveis no sistema."
        },
        "format": {
            "message": "Formato de legenda não suportado.",
            "type": "FORMAT_ERROR",
            "code": "SUBTITLE_FORMAT_INVALID",
            "suggestion": "Use formato SRT ou ASS para as legendas."
        }
    }
    
    # Detectar tipo de erro
    error_lower = error_str.lower()
    error_type = None
    error_info = None
    
    if "filenotfound" in error_lower or "no such file" in error_lower:
        error_info = error_mappings["FileNotFoundError"]
    elif "connection" in error_lower or "timeout" in error_lower or "refused" in error_lower:
        error_info = error_mappings["ConnectionError"]
    elif "ffmpeg" in error_lower or "codec" in error_lower or "encoder" in error_lower:
        error_info = error_mappings["FFmpeg"]
    elif "font" in error_lower:
        error_info = error_mappings["font"]
    elif "format" in error_lower or "srt" in error_lower or "ass" in error_lower:
        error_info = error_mappings["format"]
    elif "timeout" in error_lower:
        error_info = error_mappings["Timeout"]
    else:
        # Erro genérico
        error_info = {
            "message": "Ocorreu um erro ao processar sua solicitação.",
            "type": "UNKNOWN_ERROR",
            "code": "PROCESSING_ERROR",
            "suggestion": "Tente novamente. Se o problema persistir, entre em contato com o suporte."
        }
    
    # Construir resposta detalhada
    error_response = {
        "message": error_info["message"],
        "type": error_info["type"],
        "code": error_info["code"],
        "details": {
            "original_error": error_str[:200] if len(error_str) > 200 else error_str,
            "suggestion": error_info["suggestion"]
        }
    }
    
    # Adicionar contexto se disponível
    if context.get("video_url"):
        error_response["details"]["video_url"] = context["video_url"]
    if context.get("stage"):
        error_response["details"]["stage"] = context["stage"]
    if context.get("available_fonts"):
        error_response["details"]["available_fonts"] = context["available_fonts"]
    
    return error_response

def normalize_swagger_format_to_internal(data):
    """
    Converte o formato Swagger (subtitles_url, position, style) para o formato interno (captions, settings).
    
    Args:
        data: Dicionário com dados da requisição
    
    Returns:
        Dicionário normalizado no formato interno
    """
    normalized = data.copy()
    
    # Converter subtitles_url para captions
    if 'subtitles_url' in data and 'captions' not in data:
        normalized['captions'] = data['subtitles_url']
        del normalized['subtitles_url']
    
    # Converter position e style de nível superior para dentro de settings
    if 'settings' not in normalized:
        normalized['settings'] = {}
    
    # Mover position para dentro de settings
    if 'position' in data and isinstance(data['position'], dict):
        position_data = data['position']
        if 'position' in position_data:
            normalized['settings']['position'] = position_data['position']
        if 'x' in position_data:
            normalized['settings']['x'] = position_data['x']
        if 'y' in position_data:
            normalized['settings']['y'] = position_data['y']
        # Remover position de nível superior se foi movido
        if 'position' in normalized and normalized['position'] == data['position']:
            del normalized['position']
    
    # Mover style para dentro de settings
    if 'style' in data and isinstance(data['style'], dict):
        style_data = data['style']
        for key in ['font_family', 'font_size', 'font_color', 'background_color', 
                   'background_opacity', 'outline_color', 'outline_width', 
                   'alignment', 'bold', 'italic']:
            if key in style_data:
                normalized['settings'][key] = style_data[key]
        # Remover style de nível superior se foi movido
        if 'style' in normalized and normalized['style'] == data['style']:
            del normalized['style']
    
    return normalized

@v1_video_caption_bp.route('/v1/video/caption', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "video_url": {"type": "string", "format": "uri"},
        "captions": {"type": "string"},
        "subtitles_url": {"type": "string", "format": "uri"},
        "settings": {
            "type": "object",
            "properties": {
                "line_color": {"type": "string"},
                "word_color": {"type": "string"},
                "outline_color": {"type": "string"},
                "all_caps": {"type": "boolean"},
                "max_words_per_line": {"type": "integer"},
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "position": {
                    "type": "string",
                    "enum": [
                        "bottom_left", "bottom_center", "bottom_right",
                        "middle_left", "middle_center", "middle_right",
                        "top_left", "top_center", "top_right"
                    ]
                },
                "alignment": {
                    "type": "string",
                    "enum": ["left", "center", "right"]
                },
                "font_family": {"type": "string"},
                "font_size": {"type": "integer"},
                "font_color": {"type": "string"},
                "background_color": {"type": "string"},
                "background_opacity": {"type": "number"},
                "bold": {"type": "boolean"},
                "italic": {"type": "boolean"},
                "underline": {"type": "boolean"},
                "strikeout": {"type": "boolean"},
                "style": {
                    "type": "string",
                    "enum": ["classic", "karaoke", "highlight", "underline", "word_by_word"]
                },
                "outline_width": {"type": "integer"},
                "spacing": {"type": "integer"},
                "angle": {"type": "integer"},
                "shadow_offset": {"type": "integer"}
            },
            "additionalProperties": False
        },
        "position": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "position": {
                    "type": "string",
                    "enum": [
                        "bottom_left", "bottom_center", "bottom_right",
                        "middle_left", "middle_center", "middle_right",
                        "top_left", "top_center", "top_right"
                    ]
                }
            },
            "additionalProperties": False
        },
        "style": {
            "type": "object",
            "properties": {
                "font_family": {"type": "string"},
                "font_size": {"type": "integer"},
                "font_color": {"type": "string"},
                "background_color": {"type": "string"},
                "background_opacity": {"type": "number"},
                "outline_color": {"type": "string"},
                "outline_width": {"type": "integer"},
                "alignment": {
                    "type": "string",
                    "enum": ["left", "center", "right"]
                },
                "bold": {"type": "boolean"},
                "italic": {"type": "boolean"}
            },
            "additionalProperties": False
        },
        "replace": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "find": {"type": "string"},
                    "replace": {"type": "string"}
                },
                "required": ["find", "replace"]
            }
        },
        "exclude_time_ranges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": { "type": "string" },
                    "end": { "type": "string" }
                },
                "required": ["start", "end"],
                "additionalProperties": False
            }
        },
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "language": {"type": "string"}
    },
    "required": ["video_url"],
    "additionalProperties": True
})
@queue_task_wrapper(bypass_queue=False)
def caption_video_v1(job_id, data):
    # Normalizar formato Swagger para formato interno
    data = normalize_swagger_format_to_internal(data)
    
    video_url = data['video_url']
    captions = data.get('captions')
    settings = data.get('settings', {})
    
    # Mapear campos Swagger (font_color, background_color) para campos internos (line_color, box_color)
    if 'font_color' in settings and 'line_color' not in settings:
        settings['line_color'] = settings.pop('font_color')
    if 'background_color' in settings and 'box_color' not in settings:
        settings['box_color'] = settings.pop('background_color')
    
    replace = data.get('replace', [])
    exclude_time_ranges = data.get('exclude_time_ranges', [])
    webhook_url = data.get('webhook_url')
    id = data.get('id')
    language = data.get('language', 'auto')

    # Inicializar monitoramento
    processing_steps = []
    start_time = time.time()
    current_stage = "initialization"
    
    logger.info(f"Job {job_id}: Received v1 captioning request for {video_url}")
    logger.info(f"Job {job_id}: Settings received: {settings}")
    logger.info(f"Job {job_id}: Replace rules received: {replace}")
    logger.info(f"Job {job_id}: Exclude time ranges received: {exclude_time_ranges}")
    
    # Log status inicial
    log_job_status(job_id, {
        "job_status": "running",
        "job_id": job_id,
        "stage": current_stage,
        "processing_steps": processing_steps,
        "video_url": video_url
    })

    try:
        # STAGE 1: Geração de ASS
        current_stage = "ass_generation"
        step_start = time.time()
        processing_steps.append({
            "stage": current_stage,
            "started_at": step_start,
            "status": "started"
        })
        log_job_status(job_id, {
            "job_status": "running",
            "job_id": job_id,
            "stage": current_stage,
            "processing_steps": processing_steps
        })
        
        logger.info(f"Job {job_id}: [STAGE: {current_stage}] Starting ASS generation")
        
        # Process video with the enhanced v1 service
        output = generate_ass_captions_v1(video_url, captions, settings, replace, exclude_time_ranges, job_id, language)
        
        if isinstance(output, dict) and 'error' in output:
            # Check if this is a font-related error by checking for 'available_fonts' key
            error_context = {
                "video_url": video_url,
                "stage": current_stage
            }
            if 'available_fonts' in output:
                error_context["available_fonts"] = output['available_fonts']
                error_info = get_humanized_error_message(output['error'], error_context)
                error_info["available_fonts"] = output['available_fonts']
                processing_steps[-1].update({
                    "status": "failed",
                    "completed_at": time.time(),
                    "duration": time.time() - step_start,
                    "error": error_info
                })
                log_job_status(job_id, {
                    "job_status": "failed",
                    "job_id": job_id,
                    "stage": current_stage,
                    "processing_steps": processing_steps,
                    "error_details": error_info
                })
                return {"error": error_info}, "/v1/video/caption", 400
            else:
                error_info = get_humanized_error_message(output['error'], error_context)
                processing_steps[-1].update({
                    "status": "failed",
                    "completed_at": time.time(),
                    "duration": time.time() - step_start,
                    "error": error_info
                })
                log_job_status(job_id, {
                    "job_status": "failed",
                    "job_id": job_id,
                    "stage": current_stage,
                    "processing_steps": processing_steps,
                    "error_details": error_info
                })
                return {"error": error_info}, "/v1/video/caption", 400

        # If processing was successful, output is the ASS file path
        ass_path = output
        processing_steps[-1].update({
            "status": "completed",
            "completed_at": time.time(),
            "duration": time.time() - step_start,
            "output": ass_path
        })
        logger.info(f"Job {job_id}: [STAGE: {current_stage}] ASS file generated at {ass_path}")

        # Prepare output filename and path for the rendered video
        output_filename = f"{job_id}_captioned.mp4"
        output_path = os.path.join(os.path.dirname(ass_path), output_filename)

        # STAGE 2: Download do vídeo
        current_stage = "video_download"
        step_start = time.time()
        processing_steps.append({
            "stage": current_stage,
            "started_at": step_start,
            "status": "started"
        })
        log_job_status(job_id, {
            "job_status": "running",
            "job_id": job_id,
            "stage": current_stage,
            "processing_steps": processing_steps
        })
        
        logger.info(f"Job {job_id}: [STAGE: {current_stage}] Starting video download")
        
        video_path = None
        try:
            from services.file_management import download_file
            from config import LOCAL_STORAGE_PATH
            video_path = download_file(video_url, LOCAL_STORAGE_PATH)
            processing_steps[-1].update({
                "status": "completed",
                "completed_at": time.time(),
                "duration": time.time() - step_start,
                "output": video_path
            })
            logger.info(f"Job {job_id}: [STAGE: {current_stage}] Video downloaded to {video_path}")
        except Exception as e:
            error_context = {
                "video_url": video_url,
                "stage": current_stage
            }
            error_info = get_humanized_error_message(e, error_context)
            processing_steps[-1].update({
                "status": "failed",
                "completed_at": time.time(),
                "duration": time.time() - step_start,
                "error": error_info
            })
            logger.error(f"Job {job_id}: [STAGE: {current_stage}] Video download error: {str(e)}")
            log_job_status(job_id, {
                "job_status": "failed",
                "job_id": job_id,
                "stage": current_stage,
                "processing_steps": processing_steps,
                "error_details": error_info
            })
            return {"error": error_info}, "/v1/video/caption", 500

        # STAGE 3: Processamento FFmpeg
        current_stage = "ffmpeg_processing"
        step_start = time.time()
        processing_steps.append({
            "stage": current_stage,
            "started_at": step_start,
            "status": "started"
        })
        log_job_status(job_id, {
            "job_status": "running",
            "job_id": job_id,
            "stage": current_stage,
            "processing_steps": processing_steps
        })
        
        logger.info(f"Job {job_id}: [STAGE: {current_stage}] Starting FFmpeg processing")
        
        try:
            import ffmpeg
            ffmpeg.input(video_path).output(
                output_path,
                vf=f"subtitles='{ass_path}'",
                acodec='copy'
            ).run(overwrite_output=True)
            processing_steps[-1].update({
                "status": "completed",
                "completed_at": time.time(),
                "duration": time.time() - step_start,
                "output": output_path
            })
            logger.info(f"Job {job_id}: [STAGE: {current_stage}] FFmpeg processing completed. Output saved to {output_path}")
        except Exception as e:
            error_context = {
                "video_url": video_url,
                "stage": current_stage
            }
            error_info = get_humanized_error_message(f"FFmpeg: {str(e)}", error_context)
            processing_steps[-1].update({
                "status": "failed",
                "completed_at": time.time(),
                "duration": time.time() - step_start,
                "error": error_info
            })
            logger.error(f"Job {job_id}: [STAGE: {current_stage}] FFmpeg error: {str(e)}")
            log_job_status(job_id, {
                "job_status": "failed",
                "job_id": job_id,
                "stage": current_stage,
                "processing_steps": processing_steps,
                "error_details": error_info
            })
            return {"error": error_info}, "/v1/video/caption", 500

        # Clean up the ASS file after use
        try:
            os.remove(ass_path)
            logger.info(f"Job {job_id}: Cleaned up ASS file: {ass_path}")
        except Exception as e:
            logger.warning(f"Job {job_id}: Could not remove ASS file {ass_path}: {str(e)}")

        # STAGE 4: Upload
        current_stage = "upload"
        step_start = time.time()
        processing_steps.append({
            "stage": current_stage,
            "started_at": step_start,
            "status": "started"
        })
        log_job_status(job_id, {
            "job_status": "running",
            "job_id": job_id,
            "stage": current_stage,
            "processing_steps": processing_steps
        })
        
        logger.info(f"Job {job_id}: [STAGE: {current_stage}] Starting upload")
        
        try:
            cloud_url = upload_file(output_path)
            processing_steps[-1].update({
                "status": "completed",
                "completed_at": time.time(),
                "duration": time.time() - step_start,
                "output": cloud_url
            })
            logger.info(f"Job {job_id}: [STAGE: {current_stage}] Captioned video uploaded to cloud storage: {cloud_url}")
        except Exception as e:
            error_context = {
                "video_url": video_url,
                "stage": current_stage
            }
            error_info = get_humanized_error_message(e, error_context)
            processing_steps[-1].update({
                "status": "failed",
                "completed_at": time.time(),
                "duration": time.time() - step_start,
                "error": error_info
            })
            logger.error(f"Job {job_id}: [STAGE: {current_stage}] Upload error: {str(e)}")
            log_job_status(job_id, {
                "job_status": "failed",
                "job_id": job_id,
                "stage": current_stage,
                "processing_steps": processing_steps,
                "error_details": error_info
            })
            return {"error": error_info}, "/v1/video/caption", 500

        # Clean up the output file after upload
        # Em modo local, manter o arquivo para facilitar acesso
        is_local_mode = os.getenv('LOCAL_STORAGE_MODE', '').lower() == 'true'
        if not is_local_mode:
            try:
                os.remove(output_path)
                logger.info(f"Job {job_id}: Cleaned up local output file: {output_path}")
            except Exception as e:
                logger.warning(f"Job {job_id}: Could not remove output file {output_path}: {str(e)}")
        else:
            logger.info(f"Job {job_id}: Modo local ativo - arquivo mantido em: {output_path}")

        # Log status final de sucesso
        total_duration = time.time() - start_time
        log_job_status(job_id, {
            "job_status": "done",
            "job_id": job_id,
            "stage": "completed",
            "processing_steps": processing_steps,
            "total_duration": total_duration,
            "response": cloud_url
        })

        return cloud_url, "/v1/video/caption", 200

    except Exception as e:
        error_context = {
            "video_url": video_url,
            "stage": current_stage
        }
        error_info = get_humanized_error_message(e, error_context)
        processing_steps.append({
            "stage": "exception",
            "started_at": time.time(),
            "status": "failed",
            "error": error_info
        })
        logger.error(f"Job {job_id}: Error during captioning process - {str(e)}", exc_info=True)
        log_job_status(job_id, {
            "job_status": "failed",
            "job_id": job_id,
            "stage": current_stage,
            "processing_steps": processing_steps,
            "error_details": error_info
        })
        return {"error": error_info}, "/v1/video/caption", 500
