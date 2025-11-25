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



from functools import wraps
from flask import request, abort
from config import API_KEY
import logging

logger = logging.getLogger(__name__)

def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log de entrada
        endpoint = request.path
        method = request.method
        logger.info(f"[AUTH] Recebendo requisição | Endpoint: {endpoint} | Método: {method}")
        
        # Suportar tanto X-API-Key quanto x-api-key (minúsculo)
        api_key = request.headers.get('X-API-Key') or request.headers.get('x-api-key')
        
        # Log de validação
        if not api_key:
            logger.warning(f"[AUTH] ⚠️ API key ausente | Endpoint: {endpoint}")
            # Retornar dict ao invés de jsonify para compatibilidade com Flask-RESTX
            abort(401, description="Unauthorized")
        
        logger.info(f"[AUTH] API key presente | Endpoint: {endpoint} | Key length: {len(api_key)}")
        
        # Comparar API keys
        if api_key != API_KEY:
            logger.warning(f"[AUTH] ❌ API key inválida | Endpoint: {endpoint} | Key recebida: {api_key[:10]}...")
            # Retornar dict ao invés de jsonify para compatibilidade com Flask-RESTX
            abort(401, description="Unauthorized")
        
        logger.info(f"[AUTH] ✅ Autenticação bem-sucedida | Endpoint: {endpoint}")
        return func(*args, **kwargs)
    return wrapper
