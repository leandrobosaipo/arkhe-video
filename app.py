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



from flask import Flask, request
from flask_restx import Api, Resource, fields, Namespace
from queue import Queue
from services.webhook import send_webhook
import threading
import uuid
import os
import time
import json
import logging
from version import BUILD_NUMBER  # Import the BUILD_NUMBER
from app_utils import log_job_status, discover_and_register_blueprints  # Import the discover_and_register_blueprints function
from routes.restx_resources import register_restx_namespaces
from services.gcp_toolkit import trigger_cloud_run_job

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sanitize_for_json(obj):
    """
    Sanitiza recursivamente objetos para garantir serialização JSON segura.
    Converte bytes para string, valida tipos aninhados, e trata exceções.
    
    Args:
        obj: Objeto a ser sanitizado (dict, list, bytes, ou tipo primitivo)
    
    Returns:
        Objeto sanitizado e serializável em JSON
    """
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    elif isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        # Para tipos desconhecidos, converter para string
        try:
            return str(obj)
        except Exception:
            return None

def inspect_and_sanitize_response(response_data, job_id, logger_instance):
    """
    Inspeciona e sanitiza response[0] ANTES de usar.
    Retorna o objeto sanitizado e logs detalhados.
    """
    if response_data is None:
        logger_instance.info(f"Job {job_id}: [INSPECT] response[0] é None")
        return None
    
    # Log do tipo ANTES de sanitizar
    data_type = type(response_data).__name__
    logger_instance.info(f"Job {job_id}: [INSPECT] Tipo de response[0]: {data_type}")
    
    # Se for bytes, logar tamanho
    if isinstance(response_data, bytes):
        logger_instance.warning(f"Job {job_id}: [INSPECT] ⚠️ response[0] é BYTES! Tamanho: {len(response_data)} bytes")
        sanitized = sanitize_for_json(response_data)
        logger_instance.info(f"Job {job_id}: [INSPECT] ✅ Bytes convertidos para string. Tamanho string: {len(sanitized)} chars")
        return sanitized
    
    # Se for dict, verificar se tem bytes dentro
    if isinstance(response_data, dict):
        logger_instance.info(f"Job {job_id}: [INSPECT] response[0] é dict com {len(response_data)} chaves")
        # Verificar cada chave
        for key, value in response_data.items():
            if isinstance(value, bytes):
                logger_instance.warning(f"Job {job_id}: [INSPECT] ⚠️ Chave '{key}' contém BYTES! Tamanho: {len(value)} bytes")
            elif isinstance(value, dict):
                logger_instance.info(f"Job {job_id}: [INSPECT] Chave '{key}' é dict aninhado")
            elif isinstance(value, list):
                logger_instance.info(f"Job {job_id}: [INSPECT] Chave '{key}' é list com {len(value)} itens")
        # Sanitizar recursivamente
        sanitized = sanitize_for_json(response_data)
        logger_instance.info(f"Job {job_id}: [INSPECT] ✅ Dict sanitizado")
        return sanitized
    
    # Se for list, verificar se tem bytes dentro
    if isinstance(response_data, list):
        logger_instance.info(f"Job {job_id}: [INSPECT] response[0] é list com {len(response_data)} itens")
        # Verificar cada item
        for i, item in enumerate(response_data):
            if isinstance(item, bytes):
                logger_instance.warning(f"Job {job_id}: [INSPECT] ⚠️ Item[{i}] contém BYTES! Tamanho: {len(item)} bytes")
        # Sanitizar recursivamente
        sanitized = sanitize_for_json(response_data)
        logger_instance.info(f"Job {job_id}: [INSPECT] ✅ List sanitizada")
        return sanitized
    
    # Outros tipos
    logger_instance.info(f"Job {job_id}: [INSPECT] response[0] é {data_type}, sanitizando...")
    sanitized = sanitize_for_json(response_data)
    logger_instance.info(f"Job {job_id}: [INSPECT] ✅ {data_type} sanitizado")
    return sanitized

MAX_QUEUE_LENGTH = int(os.environ.get('MAX_QUEUE_LENGTH', 0))

def create_app():
    app = Flask(__name__)

    # Configure Flask-RESTX API (replaces Flasgger)
    api = Api(
        app,
        version=str(BUILD_NUMBER),
        title='Arkhe Video API',
        description='API para processamento de vídeo, áudio e mídia. Suporta conversão, corte, divisão, transcrição e muito mais.',
        doc='/apidocs/',
        prefix='/',
        authorizations={
            'APIKeyHeader': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'x-api-key',
                'description': 'Chave de API para autenticação. Obtenha sua chave configurando a variável de ambiente API_KEY.'
            }
        },
        security='APIKeyHeader'
    )

    # Create a queue to hold tasks
    task_queue = Queue()
    queue_id = id(task_queue)  # Generate a single queue_id for this worker

    # Function to process tasks from the queue
    def process_queue():
        while True:
            job_id, data, task_func, queue_start_time = task_queue.get()
            queue_time = time.time() - queue_start_time
            run_start_time = time.time()
            pid = os.getpid()  # Get the PID of the actual processing thread
            
            # Log job status as running
            log_job_status(job_id, {
                "job_status": "running",
                "job_id": job_id,
                "queue_id": queue_id,
                "process_id": pid,
                "response": None
            })
            
            response = task_func()
            run_time = time.time() - run_start_time
            total_time = time.time() - queue_start_time

            # SANITIZAR response[0] ANTES de usar
            logger.info(f"Job {job_id}: [QUEUE] Função executada | Status: {response[2]}")
            sanitized_response = inspect_and_sanitize_response(response[0] if response[2] == 200 else None, job_id, logger)

            response_data = {
                "endpoint": response[1],
                "code": response[2],
                "id": data.get("id"),
                "job_id": job_id,
                "response": sanitized_response,  # ← JÁ SANITIZADO
                "message": "success" if response[2] == 200 else str(response[0]),
                "pid": pid,
                "queue_id": queue_id,
                "run_time": round(run_time, 3),
                "queue_time": round(queue_time, 3),
                "total_time": round(total_time, 3),
                "queue_length": task_queue.qsize(),
                "build_number": BUILD_NUMBER  # Add build number to response
            }
            
            # Validar serialização
            try:
                json.dumps(response_data)
            except Exception as e:
                logger.error(f"Job {job_id}: [QUEUE ERRO] Serialização falhou: {str(e)}")
                response_data = sanitize_for_json(response_data)
            
            # Log job status as done
            log_job_status(job_id, {
                "job_status": "done",
                "job_id": job_id,
                "queue_id": queue_id,
                "process_id": pid,
                "response": response_data
            })

            # Only send webhook if webhook_url has an actual value (not an empty string)
            if data.get("webhook_url") and data.get("webhook_url") != "":
                send_webhook(data.get("webhook_url"), response_data)

            task_queue.task_done()

    # Start the queue processing in a separate thread
    threading.Thread(target=process_queue, daemon=True).start()

    # Decorator to add tasks to the queue or bypass it
    def queue_task(bypass_queue=False):
        def decorator(f):
            def wrapper(*args, **kwargs):
                job_id = str(uuid.uuid4())
                data = request.json if request.is_json else {}
                pid = os.getpid()  # Get PID for non-queued tasks
                start_time = time.time()

                # If running inside a GCP Cloud Run Job instance, execute synchronously
                if os.environ.get("CLOUD_RUN_JOB"):
                    # Get execution name from Google's env var
                    execution_name = os.environ.get("CLOUD_RUN_EXECUTION", "gcp_job")

                    # Log job status as running
                    log_job_status(job_id, {
                        "job_status": "running",
                        "job_id": job_id,
                        "queue_id": execution_name,
                        "process_id": pid,
                        "response": None
                    })

                    # Execute the function directly (no queue)
                    logger.info(f"Job {job_id}: [CLOUD_RUN] Executando função...")
                    response = f(job_id=job_id, data=data, *args, **kwargs)
                    run_time = time.time() - start_time

                    logger.info(f"Job {job_id}: [CLOUD_RUN] Função executada | Status: {response[2]}")
                    # SANITIZAR ANTES
                    sanitized_response = inspect_and_sanitize_response(response[0] if response[2] == 200 else None, job_id, logger)

                    # Build response object
                    response_obj = {
                        "endpoint": response[1],
                        "code": response[2],
                        "id": data.get("id"),
                        "job_id": job_id,
                        "response": sanitized_response,  # ← JÁ SANITIZADO
                        "message": "success" if response[2] == 200 else str(response[0]),
                        "run_time": round(run_time, 3),
                        "queue_time": 0,
                        "total_time": round(run_time, 3),
                        "pid": pid,
                        "queue_id": execution_name,
                        "queue_length": 0,
                        "build_number": BUILD_NUMBER
                    }
                    
                    # Validar
                    try:
                        json.dumps(response_obj)
                        logger.info(f"Job {job_id}: [CLOUD_RUN] ✅ Serialização OK")
                    except Exception as e:
                        logger.error(f"Job {job_id}: [CLOUD_RUN ERRO] Serialização falhou: {str(e)}")
                        response_obj = sanitize_for_json(response_obj)

                    # Log job status as done
                    log_job_status(job_id, {
                        "job_status": "done",
                        "job_id": job_id,
                        "queue_id": execution_name,
                        "process_id": pid,
                        "response": response_obj
                    })

                    # Send webhook if webhook_url is provided
                    if data.get("webhook_url") and data.get("webhook_url") != "":
                        send_webhook(data.get("webhook_url"), response_obj)

                    return response_obj, response[2]

                if os.environ.get("GCP_JOB_NAME") and data.get("webhook_url"):
                    try:
                        overrides = {
                            'container_overrides': [
                                {
                                    'env': [
                                        # Environment variables to pass to the GCP Cloud Run Job
                                        {
                                            'name': 'GCP_JOB_PATH',
                                            'value': request.path  # Endpoint to call
                                        },
                                        {
                                            'name': 'GCP_JOB_PAYLOAD',
                                            'value': json.dumps(data)  # Payload as a string
                                        },
                                    ]
                                }
                            ],
                            'task_count': 1
                        }

                        # Call trigger_cloud_run_job with the overrides dictionary
                        response = trigger_cloud_run_job(
                            job_name=os.environ.get("GCP_JOB_NAME"),
                            location=os.environ.get("GCP_JOB_LOCATION", "us-central1"),
                            overrides=overrides  # Pass overrides to the job
                        )

                        if not response.get("job_submitted"):
                            raise Exception(f"GCP job trigger failed: {response}")

                        # Extract execution name and short ID for tracking
                        execution_name = response.get("execution_name", "")
                        gcp_queue_id = execution_name.split('/')[-1] if execution_name else "gcp_job"

                        # Prepare the response object
                        # Sanitizar response antes de usar
                        sanitized_message = sanitize_for_json(response) if isinstance(response, (dict, list)) else response
                        response_obj = {
                            "code": 200,
                            "id": data.get("id"),
                            "job_id": job_id,
                            "message": sanitized_message,  # ← JÁ SANITIZADO
                            "job_name": os.environ.get("GCP_JOB_NAME"),
                            "location": os.environ.get("GCP_JOB_LOCATION", "us-central1"),
                            "pid": pid,
                            "queue_id": gcp_queue_id,
                            "build_number": BUILD_NUMBER
                        }
                        
                        # Validar
                        try:
                            json.dumps(response_obj)
                        except Exception as e:
                            logger.error(f"Job {job_id}: [GCP_SUBMIT ERRO] Serialização falhou: {str(e)}")
                            response_obj = sanitize_for_json(response_obj)
                        log_job_status(job_id, {
                            "job_status": "submitted",
                            "job_id": job_id,
                            "queue_id": gcp_queue_id,
                            "process_id": pid,
                            "response": response_obj
                        })
                        return response_obj, 200  # Return 200 since it's a submission success

                    except Exception as e:
                        error_message = f"GCP Cloud Run Job trigger failed: {str(e)}"
                        error_response = {
                            "code": 500,
                            "id": data.get("id"),
                            "job_id": job_id,
                            "message": error_message,  # Já é string, não precisa sanitizar
                            "job_name": os.environ.get("GCP_JOB_NAME"),
                            "location": os.environ.get("GCP_JOB_LOCATION", "us-central1"),
                            "pid": pid,
                            "queue_id": "gcp_job",
                            "build_number": BUILD_NUMBER
                        }
                        
                        # Validar (mesmo sendo erro, precisa ser serializável)
                        try:
                            json.dumps(error_response)
                        except Exception as e2:
                            logger.error(f"Job {job_id}: [GCP_ERROR ERRO] Serialização falhou: {str(e2)}")
                            error_response = sanitize_for_json(error_response)
                        log_job_status(job_id, {
                            "job_status": "failed",
                            "job_id": job_id,
                            "queue_id": "gcp_job",
                            "process_id": pid,
                            "response": error_response
                        })
                        return error_response, 500

                elif bypass_queue or 'webhook_url' not in data:
                    
                    # Log ANTES de executar
                    logger.info(f"Job {job_id}: [00] Recebendo requisição | Endpoint: {request.path} | Método: {request.method}")
                    logger.info(f"Job {job_id}: [01] Modo: bypass_queue={bypass_queue} | webhook_url presente: {'webhook_url' in data}")
                    
                    # Log job status as running immediately (bypassing queue)
                    log_job_status(job_id, {
                        "job_status": "running",
                        "job_id": job_id,
                        "queue_id": queue_id,
                        "process_id": pid,
                        "response": None
                    })
                    
                    # Log ANTES de executar função
                    logger.info(f"Job {job_id}: [02] Executando função do endpoint...")
                    
                    try:
                        response = f(job_id=job_id, data=data, *args, **kwargs)
                        run_time = time.time() - start_time
                        
                        # Log DEPOIS de executar - ANTES de criar response_obj
                        logger.info(f"Job {job_id}: [03] Função executada | Tempo: {run_time:.3f}s | Status code: {response[2]}")
                        logger.info(f"Job {job_id}: [04] Inspecionando response[0] ANTES de criar response_obj...")
                        
                        # SANITIZAR response[0] ANTES de usar
                        sanitized_response = None
                        if response[2] == 200:
                            sanitized_response = inspect_and_sanitize_response(response[0], job_id, logger)
                        else:
                            # Se não for 200, response[0] é a mensagem de erro (string)
                            logger.info(f"Job {job_id}: [04] Status não é 200, response[0] é mensagem de erro")
                            sanitized_response = str(response[0]) if response[0] else None
                        
                        # Log ANTES de criar response_obj
                        logger.info(f"Job {job_id}: [05] Criando response_obj com dados sanitizados...")
                        
                        # Criar response_obj com dados JÁ SANITIZADOS
                        response_obj = {
                            "endpoint": response[1],
                            "code": response[2],
                            "id": data.get("id"),
                            "job_id": job_id,
                            "response": sanitized_response,  # ← JÁ SANITIZADO
                            "message": "success" if response[2] == 200 else str(response[0]),
                            "run_time": round(run_time, 3),
                            "queue_time": 0,
                            "total_time": round(run_time, 3),
                            "pid": pid,
                            "queue_id": queue_id,
                            "queue_length": task_queue.qsize(),
                            "build_number": BUILD_NUMBER
                        }
                        
                        # Log ANTES de validar serialização
                        logger.info(f"Job {job_id}: [06] Validando serialização JSON do response_obj...")
                        
                        # Validar ANTES de retornar
                        try:
                            json.dumps(response_obj)
                            logger.info(f"Job {job_id}: [07] ✅ Serialização JSON válida! Retornando resposta...")
                        except (TypeError, ValueError) as e:
                            logger.error(f"Job {job_id}: [ERRO] ❌ Serialização falhou mesmo após sanitização! | Erro: {type(e).__name__}: {str(e)}")
                            logger.error(f"Job {job_id}: [ERRO] Tipos no response_obj: endpoint={type(response_obj.get('endpoint'))}, code={type(response_obj.get('code'))}, response={type(response_obj.get('response'))}")
                            # Tentar sanitizar TUDO novamente
                            response_obj = sanitize_for_json(response_obj)
                            try:
                                json.dumps(response_obj)
                                logger.warning(f"Job {job_id}: [FALLBACK] ✅ Serialização OK após sanitização completa")
                            except Exception as e2:
                                logger.error(f"Job {job_id}: [ERRO CRÍTICO] Falha total de serialização: {str(e2)}")
                                raise ValueError(f"Erro crítico de serialização: {str(e2)}")
                        
                        # Log job status as done
                        log_job_status(job_id, {
                            "job_status": "done",
                            "job_id": job_id,
                            "queue_id": queue_id,
                            "process_id": pid,
                            "response": response_obj
                        })
                        
                        logger.info(f"Job {job_id}: [08] ✅ Resposta retornada com sucesso")
                        return response_obj, response[2]
                        
                    except Exception as e:
                        logger.error(f"Job {job_id}: [ERRO] Exceção durante execução: {type(e).__name__}: {str(e)}", exc_info=True)
                        raise
                else:
                    if MAX_QUEUE_LENGTH > 0 and task_queue.qsize() >= MAX_QUEUE_LENGTH:
                        error_message = f"MAX_QUEUE_LENGTH ({MAX_QUEUE_LENGTH}) reached"
                        error_response = {
                            "code": 429,
                            "id": data.get("id"),
                            "job_id": job_id,
                            "message": error_message,  # Já é string
                            "pid": pid,
                            "queue_id": queue_id,
                            "queue_length": task_queue.qsize(),
                            "build_number": BUILD_NUMBER  # Add build number to response
                        }
                        
                        # Validar
                        try:
                            json.dumps(error_response)
                        except Exception as e:
                            logger.error(f"Job {job_id}: [QUEUE_FULL ERRO] Serialização falhou: {str(e)}")
                            error_response = sanitize_for_json(error_response)
                        
                        # Log the queue overflow error
                        log_job_status(job_id, {
                            "job_status": "done",
                            "job_id": job_id,
                            "queue_id": queue_id,
                            "process_id": pid,
                            "response": error_response
                        })
                        
                        return error_response, 429
                    
                    # Log job status as queued
                    log_job_status(job_id, {
                        "job_status": "queued",
                        "job_id": job_id,
                        "queue_id": queue_id,
                        "process_id": pid,
                        "response": None
                    })
                    
                    task_queue.put((job_id, data, lambda: f(job_id=job_id, data=data, *args, **kwargs), start_time))
                    
                    response_202 = {
                        "code": 202,
                        "id": data.get("id"),
                        "job_id": job_id,
                        "message": "processing",
                        "pid": pid,
                        "queue_id": queue_id,
                        "max_queue_length": MAX_QUEUE_LENGTH if MAX_QUEUE_LENGTH > 0 else "unlimited",
                        "queue_length": task_queue.qsize(),
                        "build_number": BUILD_NUMBER  # Add build number to response
                    }
                    
                    # Validar
                    try:
                        json.dumps(response_202)
                    except Exception as e:
                        logger.error(f"Job {job_id}: [QUEUED_202 ERRO] Serialização falhou: {str(e)}")
                        response_202 = sanitize_for_json(response_202)
                    
                    return response_202, 202
            return wrapper
        return decorator

    app.queue_task = queue_task
    app.api = api  # Make API available to routes for namespace registration

    # Register special route for Next.js root asset paths first
    from routes.v1.media.feedback import create_root_next_routes
    create_root_next_routes(app)
    
    # Use the discover_and_register_blueprints function to register all blueprints
    discover_and_register_blueprints(app)
    
    # Register Flask-RESTX namespaces for Swagger documentation
    register_restx_namespaces(api)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)