# Schemas compartilhados para Swagger
# Este arquivo contém definições reutilizáveis para documentação da API

COMMON_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {
            "type": "integer",
            "description": "Código HTTP da resposta",
            "example": 200
        },
        "endpoint": {
            "type": "string",
            "description": "Endpoint chamado",
            "example": "/v1/video/split"
        },
        "id": {
            "type": "string",
            "description": "ID opcional fornecido na requisição",
            "example": "custom-request-id"
        },
        "job_id": {
            "type": "string",
            "description": "ID único do job gerado pelo sistema",
            "example": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
        },
        "message": {
            "type": "string",
            "description": "Mensagem de status",
            "example": "success"
        },
        "response": {
            "description": "Dados da resposta (varia conforme o endpoint)"
        },
        "pid": {
            "type": "integer",
            "description": "Process ID do worker que processou a requisição",
            "example": 12345
        },
        "queue_id": {
            "type": "integer",
            "description": "ID da fila de processamento",
            "example": 6789
        },
        "run_time": {
            "type": "number",
            "description": "Tempo de execução em segundos",
            "example": 5.234
        },
        "queue_time": {
            "type": "number",
            "description": "Tempo na fila em segundos",
            "example": 0.123
        },
        "total_time": {
            "type": "number",
            "description": "Tempo total em segundos",
            "example": 5.357
        },
        "queue_length": {
            "type": "integer",
            "description": "Tamanho atual da fila",
            "example": 0
        },
        "build_number": {
            "type": "string",
            "description": "Número da build da API",
            "example": "211"
        }
    }
}

QUEUED_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {
            "type": "integer",
            "example": 202
        },
        "id": {
            "type": "string",
            "example": "custom-request-id"
        },
        "job_id": {
            "type": "string",
            "example": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
        },
        "message": {
            "type": "string",
            "example": "processing"
        },
        "pid": {
            "type": "integer",
            "example": 12345
        },
        "queue_id": {
            "type": "integer",
            "example": 6789
        },
        "max_queue_length": {
            "type": "string",
            "example": "unlimited"
        },
        "queue_length": {
            "type": "integer",
            "example": 2
        },
        "build_number": {
            "type": "string",
            "example": "211"
        }
    }
}

ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {
            "type": "integer",
            "example": 400
        },
        "message": {
            "type": "string",
            "example": "Invalid request payload"
        },
        "id": {
            "type": "string",
            "example": "custom-request-id"
        },
        "job_id": {
            "type": "string",
            "example": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
        }
    }
}

COMMON_REQUEST_PARAMS = {
    "webhook_url": {
        "type": "string",
        "format": "uri",
        "description": "URL para receber notificação webhook quando o job for concluído",
        "example": "https://example.com/webhook"
    },
    "id": {
        "type": "string",
        "description": "ID opcional para rastreamento da requisição",
        "example": "custom-request-id"
    }
}

ENCODING_PARAMS = {
    "video_codec": {
        "type": "string",
        "description": "Codec de vídeo para encoding",
        "example": "libx264",
        "default": "libx264"
    },
    "video_preset": {
        "type": "string",
        "description": "Preset de encoding de vídeo (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)",
        "example": "medium",
        "default": "medium"
    },
    "video_crf": {
        "type": "integer",
        "description": "Constant Rate Factor para qualidade de vídeo (0-51, menor = melhor qualidade)",
        "minimum": 0,
        "maximum": 51,
        "example": 23,
        "default": 23
    },
    "audio_codec": {
        "type": "string",
        "description": "Codec de áudio para encoding",
        "example": "aac",
        "default": "aac"
    },
    "audio_bitrate": {
        "type": "string",
        "description": "Bitrate de áudio",
        "example": "128k",
        "default": "128k"
    }
}

TIME_SEGMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "start": {
            "type": "string",
            "description": "Tempo de início no formato hh:mm:ss.ms",
            "example": "00:00:10.000"
        },
        "end": {
            "type": "string",
            "description": "Tempo de fim no formato hh:mm:ss.ms",
            "example": "00:00:20.000"
        }
    },
    "required": ["start", "end"]
}

