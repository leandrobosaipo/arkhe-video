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



import os
import logging
from flask import Blueprint
from services.authentication import authenticate
from services.cloud_storage import upload_file
from app_utils import queue_task_wrapper
from config import LOCAL_STORAGE_PATH

v1_toolkit_test_bp = Blueprint('v1_toolkit_test', __name__)
logger = logging.getLogger(__name__)

@v1_toolkit_test_bp.route('/v1/toolkit/test', methods=['GET'])
@authenticate
@queue_task_wrapper(bypass_queue=True)
def test_api(job_id, data):
    """
    Testa se a API está funcionando corretamente
    ---
    tags:
      - Toolkit
    security:
      - APIKeyHeader: []
    produces:
      - application/json
    parameters:
      - in: header
        name: x-api-key
        type: string
        required: true
        description: Chave de API para autenticação
        example: sua-chave-api-aqui
    responses:
      200:
        description: API funcionando corretamente
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 200
            endpoint:
              type: string
              example: "/v1/toolkit/test"
            job_id:
              type: string
              example: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
            message:
              type: string
              example: "success"
            response:
              type: string
              format: uri
              example: "https://example.com/success.txt"
            build_number:
              type: string
              example: "211"
      401:
        description: Não autorizado - API key inválida ou ausente
      500:
        description: Erro interno do servidor
    """
    logger.info(f"Job {job_id}: Testing NCA Toolkit API setup")
    
    try:
        # Create test file
        test_filename = os.path.join(LOCAL_STORAGE_PATH, "success.txt")
        with open(test_filename, 'w') as f:
            f.write("You have successfully installed the NCA Toolkit API, great job!")
        
        # Upload file to cloud storage
        upload_url = upload_file(test_filename)
        
        # Clean up local file
        os.remove(test_filename)
        
        return upload_url, "/v1/toolkit/test", 200
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error testing API setup - {str(e)}")
        return str(e), "/v1/toolkit/test", 500