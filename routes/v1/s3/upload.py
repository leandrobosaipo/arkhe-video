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
from services.authentication import authenticate
from app_utils import validate_payload, queue_task_wrapper
from services.v1.s3.upload import stream_upload_to_s3
import os
import json
import logging

logger = logging.getLogger(__name__)
v1_s3_upload_bp = Blueprint('v1_s3_upload', __name__)

@v1_s3_upload_bp.route('/v1/s3/upload', methods=['POST'])
@authenticate
@validate_payload({
    "type": "object",
    "properties": {
        "file_url": {"type": "string", "format": "uri"},
        "filename": {"type": "string"},
        "public": {"type": "boolean"},
        "download_headers": {"type": "object"},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"}
    },
    "required": ["file_url"],
    "additionalProperties": False
})
@queue_task_wrapper(bypass_queue=False)
def s3_upload_endpoint(job_id, data):
    """
    Faz upload de um arquivo para S3 via streaming direto da URL
    ---
    tags:
      - S3
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
            - file_url
          properties:
            file_url:
              type: string
              format: uri
              description: URL do arquivo para fazer upload
              example: https://example.com/file.mp4
            filename:
              type: string
              description: Nome do arquivo no S3 (opcional, usa nome original se não especificado)
              example: my-file.mp4
            public:
              type: boolean
              description: Tornar arquivo público (padrão: false)
              example: false
            download_headers:
              type: object
              description: Headers HTTP opcionais para autenticação no download do arquivo
              example:
                Authorization: "Bearer token"
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
        description: Upload concluído com sucesso
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/s3/upload"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: string
              format: uri
              example: "https://bucket.s3.amazonaws.com/file.mp4"
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
    try:
        file_url = data.get('file_url')
        filename = data.get('filename')  # Optional, will default to original filename if not provided
        make_public = data.get('public', False)  # Default to private
        download_headers = data.get('download_headers')  # Optional headers for authentication
        
        logger.info(f"Job {job_id}: Starting S3 streaming upload from {file_url}")
        
        # Call the service function to handle the upload
        result = stream_upload_to_s3(file_url, filename, make_public, download_headers)
        
        logger.info(f"Job {job_id}: Successfully uploaded to S3")
        
        return result, "/v1/s3/upload", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error streaming upload to S3 - {str(e)}")
        return str(e), "/v1/s3/upload", 500