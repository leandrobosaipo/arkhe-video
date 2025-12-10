# Registro de Resources Flask-RESTX para documentação Swagger
# Este arquivo registra endpoints principais no Flask-RESTX para aparecerem no Swagger

from flask_restx import Namespace, Resource, fields
from flask import request, current_app
from services.authentication import authenticate
import logging

logger = logging.getLogger(__name__)

# Criar namespaces
toolkit_ns = Namespace('Toolkit', description='Endpoints utilitários da API')
video_ns = Namespace('Video', description='Endpoints para processamento de vídeo')
audio_ns = Namespace('Audio', description='Endpoints para processamento de áudio')
media_ns = Namespace('Media', description='Endpoints para processamento de mídia geral')
s3_ns = Namespace('S3', description='Endpoints para upload S3')
image_ns = Namespace('Image', description='Endpoints para processamento de imagens')
gcp_ns = Namespace('GCP', description='Endpoints para Google Cloud Platform')
ffmpeg_ns = Namespace('FFmpeg', description='Endpoints para operações FFmpeg avançadas')
code_ns = Namespace('Code', description='Endpoints para execução de código')

# Modelos de resposta comuns
success_response_model = toolkit_ns.model('SuccessResponse', {
    'code': fields.Integer(example=200),
    'endpoint': fields.String(example='/v1/toolkit/test'),
    'job_id': fields.String(example='a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6'),
    'message': fields.String(example='success'),
    'response': fields.Raw(description='Resposta do endpoint'),
    'build_number': fields.String(example='211')
})

# ============================================================================
# MODELOS REUTILIZÁVEIS
# ============================================================================

# Modelos comuns para todos os endpoints
webhook_url_field = fields.String(
    description='URL para receber notificação quando o job for concluído. Onde conseguir: URL pública do seu webhook (ex: n8n, Zapier, Make). Onde interfere: Se fornecido, a resposta será enviada via POST para esta URL quando o processamento terminar, permitindo processamento assíncrono.',
    example='https://example.com/webhook'
)

id_field = fields.String(
    description='ID customizado para rastreamento da requisição. Onde conseguir: Qualquer string única que você queira usar para identificar esta requisição. Onde interfere: Este ID será retornado na resposta para facilitar o rastreamento.',
    example='custom-request-id-123'
)

# Modelos de codec e encoding
video_codec_field = fields.String(
    description='Codec de vídeo para encoding. Onde conseguir: Valores comuns: libx264 (H.264, mais compatível), libx265 (H.265/HEVC, melhor compressão), vp9 (WebM). Onde interfere: Afeta qualidade, tamanho do arquivo e compatibilidade. Variações: libx264 = melhor compatibilidade, libx265 = menor tamanho, vp9 = melhor para web.',
    example='libx264',
    default='libx264'
)

video_preset_field = fields.String(
    description='Preset de encoding que controla velocidade vs qualidade. Onde conseguir: Valores: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow. Onde interfere: Valores mais rápidos = processamento mais rápido mas arquivo maior. Variações: ultrafast = muito rápido mas arquivo grande, veryslow = muito lento mas arquivo pequeno.',
    example='medium',
    default='medium',
    enum=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']
)

video_crf_field = fields.Integer(
    description='Constant Rate Factor - controla qualidade do vídeo (0-51). Onde conseguir: Número inteiro entre 0 e 51. Onde interfere: Valores menores = melhor qualidade mas arquivo maior. Variações: 18 = qualidade muito alta, 23 = qualidade padrão, 28 = qualidade menor mas arquivo pequeno.',
    example=23,
    default=23,
    min=0,
    max=51
)

audio_codec_field = fields.String(
    description='Codec de áudio para encoding. Onde conseguir: Valores comuns: aac (mais compatível), mp3, opus, vorbis. Onde interfere: Afeta qualidade e compatibilidade do áudio. Variações: aac = melhor compatibilidade, opus = melhor qualidade para web.',
    example='aac',
    default='aac'
)

audio_bitrate_field = fields.String(
    description='Bitrate de áudio em formato Xk (ex: 128k, 192k, 256k). Onde conseguir: String no formato "Nk" onde N é o bitrate. Onde interfere: Valores maiores = melhor qualidade mas arquivo maior. Variações: 128k = qualidade padrão, 192k = melhor qualidade, 256k = alta qualidade.',
    example='128k',
    default='128k'
)

# Modelo de requisição básico com media_url
media_url_model = media_ns.model('MediaURLRequest', {
    'media_url': fields.String(
        required=True,
        description='URL pública do arquivo de mídia (vídeo, áudio ou imagem). Onde conseguir: URL de um arquivo hospedado em servidor público, S3, GCS, ou CDN. Onde interfere: O arquivo será baixado desta URL para processamento.',
        example='https://example.com/video.mp4'
    ),
    'webhook_url': webhook_url_field,
    'id': id_field
})

def call_blueprint_function(endpoint_name):
    """Helper para chamar funções de blueprint através do sistema de queue"""
    def wrapper(self):
        import logging
        logger = logging.getLogger(__name__)
        
        # Obter função do blueprint através do endpoint
        view_func = current_app.view_functions.get(endpoint_name)
        
        if not view_func:
            # Log detalhado quando não encontra
            logger.error(f"Endpoint function '{endpoint_name}' não encontrado em view_functions")
            
            # Tentar encontrar funções relacionadas para ajudar no debug
            all_functions = list(current_app.view_functions.keys())
            # Filtrar funções que podem estar relacionadas (mesmo módulo ou similar)
            endpoint_parts = endpoint_name.split('.')
            if len(endpoint_parts) >= 2:
                module_part = endpoint_parts[0]
                function_part = endpoint_parts[1]
                related_functions = [
                    name for name in all_functions
                    if module_part in name.lower() or function_part in name.lower()
                ]
            else:
                related_functions = [
                    name for name in all_functions
                    if any(part in name.lower() for part in endpoint_name.split('.'))
                ]
            
            # Log das funções relacionadas encontradas
            if related_functions:
                logger.error(f"Funções relacionadas encontradas (primeiras 10):")
                for func_name in sorted(related_functions)[:10]:
                    logger.error(f"  - {func_name}")
            else:
                logger.error(f"Nenhuma função relacionada encontrada. Total de funções registradas: {len(all_functions)}")
            
            # Retornar erro detalhado com informações úteis
            error_response = {
                'error': f'Endpoint function not found: {endpoint_name}',
                'message': f'A função do endpoint "{endpoint_name}" não foi encontrada. Verifique se o nome do blueprint e da função estão corretos.',
                'expected': endpoint_name,
                'suggestion': 'Verifique o nome do blueprint e da função no arquivo de rota. O formato esperado é: {blueprint_name}.{function_name}'
            }
            
            # Adicionar funções relacionadas se houver (limitado para não expor demais)
            if related_functions:
                error_response['available_related'] = sorted(related_functions)[:10]
            
            return error_response, 500
        
        try:
            # Chamar através do sistema de queue
            job_id = 'restx-doc'
            data = request.json if request.is_json else {}
            result = view_func(job_id=job_id, data=data)
            if isinstance(result, tuple) and len(result) == 3:
                return result[0], result[2]  # Retornar (data, status_code)
            return result
        except Exception as e:
            logger.error(f"Erro ao executar função do endpoint '{endpoint_name}': {str(e)}", exc_info=True)
            return {
                'error': f'Error executing endpoint: {str(e)}',
                'endpoint': endpoint_name,
                'message': 'Ocorreu um erro ao executar a função do endpoint. Verifique os logs do servidor para mais detalhes.'
            }, 500
    return wrapper

# Toolkit - Test
@toolkit_ns.route('/v1/toolkit/test')
@toolkit_ns.doc(security='APIKeyHeader')
class TestAPI(Resource):
    @toolkit_ns.doc(
        description='Testa se a API está funcionando corretamente',
        responses={
            200: 'API funcionando corretamente',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @toolkit_ns.marshal_with(success_response_model, code=200)
    def get(self):
        """Testa se a API está funcionando corretamente"""
        # Aplicar autenticação
        from services.authentication import authenticate
        auth_check = authenticate(lambda: None)
        auth_result = auth_check()
        if auth_result is not None:
            return auth_result
        
        return call_blueprint_function('v1_toolkit_test.test_api')(self)

# Toolkit - Authenticate
@toolkit_ns.route('/v1/toolkit/authenticate')
@toolkit_ns.doc(security='APIKeyHeader')
class AuthenticateAPI(Resource):
    @toolkit_ns.doc(
        description='Autentica uma chave de API. O que faz: Valida se a chave de API fornecida no header é válida. Onde usar: Para verificar se sua chave de API está funcionando antes de fazer requisições.',
        responses={
            200: 'Autenticação bem-sucedida - retorna "Authorized"',
            401: 'Autenticação falhou - chave inválida ou ausente'
        }
    )
    def get(self):
        """Autentica uma chave de API"""
        return call_blueprint_function('v1_toolkit_auth.authenticate_endpoint')(self)

# Toolkit - Job Status
@toolkit_ns.route('/v1/toolkit/job/status')
@toolkit_ns.doc(security='APIKeyHeader')
class JobStatusAPI(Resource):
    job_status_model = toolkit_ns.model('JobStatusRequest', {
        'job_id': fields.String(
            required=True,
            description='ID do job para consultar o status. Onde conseguir: Retornado na resposta 202 quando um job é enfileirado (campo "job_id"). Onde interfere: Usado para buscar o status atual do processamento.',
            example='a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6'
        )
    })
    
    @toolkit_ns.doc(
        description='Obtém o status detalhado de um job específico. O que faz: Retorna informações sobre o processamento de um job, incluindo status (queued, running, done, error) e resultado quando concluído. Onde usar: Para acompanhar o progresso de jobs enfileirados.',
        body=job_status_model,
        responses={
            200: 'Status do job retornado com sucesso',
            404: 'Job não encontrado',
            500: 'Erro ao buscar status'
        }
    )
    @toolkit_ns.expect(job_status_model)
    def post(self):
        """Obtém o status de um job específico"""
        return call_blueprint_function('v1_toolkit_job_status.get_job_status')(self)

# Toolkit - Jobs Status (All)
@toolkit_ns.route('/v1/toolkit/jobs/status')
@toolkit_ns.doc(security='APIKeyHeader')
class JobsStatusAPI(Resource):
    jobs_status_model = toolkit_ns.model('JobsStatusRequest', {
        'since_seconds': fields.Integer(
            description='Intervalo de tempo em segundos para buscar jobs. Onde conseguir: Número de segundos (ex: 600 = 10 minutos). Onde interfere: Apenas jobs modificados neste intervalo serão retornados. Variações: 600 = últimos 10 min, 3600 = última hora, 86400 = último dia.',
            example=600,
            default=600
        )
    })
    
    @toolkit_ns.doc(
        description='Obtém o status de todos os jobs dentro de um intervalo de tempo. O que faz: Retorna um dicionário com job_id como chave e status como valor para todos os jobs recentes. Onde usar: Para monitorar múltiplos jobs de uma vez.',
        body=jobs_status_model,
        responses={
            200: 'Status dos jobs retornado com sucesso',
            404: 'Diretório de jobs não encontrado',
            500: 'Erro ao buscar status'
        }
    )
    @toolkit_ns.expect(jobs_status_model)
    def post(self):
        """Obtém o status de todos os jobs"""
        return call_blueprint_function('v1_toolkit_jobs_status.get_all_jobs_status')(self)

# Media - Convert to MP3
@media_ns.route('/v1/media/convert/mp3')
@media_ns.doc(security='APIKeyHeader')
class ConvertToMP3(Resource):
    @media_ns.doc(
        description='Converte arquivos de mídia para formato MP3',
        body=media_url_model,
        responses={
            200: 'Conversão concluída com sucesso',
            202: 'Requisição enfileirada para processamento',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @media_ns.expect(media_url_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Converte arquivos de mídia para formato MP3"""
        return call_blueprint_function('v1_media_convert_mp3.convert_media_to_mp3')(self)

# Media - Transcribe
@media_ns.route('/v1/media/transcribe')
@media_ns.doc(security='APIKeyHeader')
class TranscribeMedia(Resource):
    transcribe_model = media_ns.model('TranscribeRequest', {
        'media_url': fields.String(
            required=True,
            description='URL pública do arquivo de mídia (vídeo ou áudio) para transcrição. Onde conseguir: URL de arquivo hospedado publicamente. Onde interfere: O arquivo será baixado e processado pelo modelo Whisper.',
            example='https://example.com/video.mp4'
        ),
        'task': fields.String(
            enum=['transcribe', 'translate'],
            description='Tipo de tarefa a realizar. Onde conseguir: "transcribe" ou "translate". Onde interfere: transcribe = mantém idioma original, translate = traduz para inglês. Variações: transcribe = texto no idioma original, translate = texto em inglês.',
            example='transcribe',
            default='transcribe'
        ),
        'include_text': fields.Boolean(
            description='Incluir texto simples na resposta. Onde conseguir: true ou false. Onde interfere: Se true, retorna campo "text" com transcrição completa. Variações: true = inclui texto, false = não inclui.',
            example=True,
            default=True
        ),
        'include_srt': fields.Boolean(
            description='Incluir arquivo SRT (legendas) na resposta. Onde conseguir: true ou false. Onde interfere: Se true, retorna campo "srt" com legendas formatadas. Variações: true = inclui SRT, false = não inclui.',
            example=False,
            default=False
        ),
        'include_segments': fields.Boolean(
            description='Incluir segmentos detalhados com timestamps. Onde conseguir: true ou false. Onde interfere: Se true, retorna array "segments" com timestamps precisos. Variações: true = inclui timestamps detalhados, false = apenas texto.',
            example=False,
            default=False
        ),
        'word_timestamps': fields.Boolean(
            description='Incluir timestamps por palavra (requer include_segments=true). Onde conseguir: true ou false. Onde interfere: Se true, cada palavra terá timestamp individual. Variações: true = timestamps por palavra, false = timestamps por frase.',
            example=False,
            default=False
        ),
        'response_type': fields.String(
            enum=['direct', 'cloud'],
            description='Tipo de resposta. Onde conseguir: "direct" ou "cloud". Onde interfere: direct = retorna dados na resposta, cloud = salva em storage e retorna URL. Variações: direct = resposta imediata, cloud = URL do arquivo.',
            example='direct',
            default='direct'
        ),
        'language': fields.String(
            description='Código do idioma para a transcrição (ISO 639-1). Onde conseguir: Código de 2 letras (ex: pt, en, es, fr). Onde interfere: Força detecção do idioma, melhora precisão. Variações: pt = português, en = inglês, auto = detecta automaticamente.',
            example='pt'
        ),
        'webhook_url': webhook_url_field,
        'words_per_line': fields.Integer(
            description='Máximo de palavras por linha no arquivo SRT. Onde conseguir: Número inteiro (mínimo 1). Onde interfere: Controla quebra de linhas nas legendas. Variações: 8 = linhas curtas, 12 = linhas médias, 15 = linhas longas.',
            example=8,
            default=8,
            min=1
        ),
        'id': id_field
    })
    
    @media_ns.doc(
        description='Transcreve ou traduz áudio/vídeo usando o modelo Whisper da OpenAI. O que faz: Baixa o arquivo de mídia, processa com Whisper e retorna transcrição/tradução. Onde usar: Para gerar legendas, transcrições ou traduções de conteúdo de áudio/vídeo. Requer: Arquivo de mídia acessível publicamente.',
        body=transcribe_model,
        responses={
            200: 'Transcrição concluída com sucesso - retorna texto, SRT e/ou segments conforme solicitado',
            202: 'Requisição enfileirada para processamento assíncrono',
            400: 'Requisição inválida - verifique parâmetros',
            401: 'Não autorizado - API key inválida',
            500: 'Erro interno do servidor'
        }
    )
    @media_ns.expect(transcribe_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Transcreve ou traduz áudio/vídeo usando Whisper"""
        return call_blueprint_function('v1_media_transcribe.transcribe')(self)

# Media - Convert
@media_ns.route('/v1/media/convert')
@media_ns.doc(security='APIKeyHeader')
class ConvertMedia(Resource):
    convert_model = media_ns.model('ConvertMediaRequest', {
        'media_url': fields.String(
            required=True,
            description='URL pública do arquivo de mídia para conversão. Onde conseguir: URL de arquivo hospedado. Onde interfere: Arquivo será baixado e convertido para o formato especificado.',
            example='https://example.com/video.mp4'
        ),
        'format': fields.String(
            required=True,
            description='Formato de saída desejado. Onde conseguir: Extensão do formato (mp4, avi, mov, webm, mkv, flv). Onde interfere: Define o container do arquivo de saída. Variações: mp4 = mais compatível, webm = melhor para web, mkv = melhor qualidade.',
            example='mp4'
        ),
        'video_codec': video_codec_field,
        'video_preset': video_preset_field,
        'video_crf': video_crf_field,
        'audio_codec': audio_codec_field,
        'audio_bitrate': audio_bitrate_field,
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @media_ns.doc(
        description='Converte arquivos de mídia entre diferentes formatos com controle total sobre codecs e qualidade. O que faz: Baixa o arquivo, converte para o formato especificado e faz upload para cloud storage. Onde usar: Para converter vídeos/áudios entre formatos ou ajustar codecs.',
        body=convert_model,
        responses={
            200: 'Conversão concluída - retorna URL do arquivo convertido',
            202: 'Requisição enfileirada',
            400: 'Formato inválido ou não suportado',
            401: 'Não autorizado',
            500: 'Erro na conversão'
        }
    )
    @media_ns.expect(convert_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Converte arquivos de mídia entre formatos"""
        return call_blueprint_function('v1_media_convert.convert_media_format')(self)

# Media - Metadata
@media_ns.route('/v1/media/metadata')
@media_ns.doc(security='APIKeyHeader')
class MediaMetadata(Resource):
    metadata_model = media_ns.model('MetadataRequest', {
        'media_url': fields.String(
            required=True,
            description='URL pública do arquivo de mídia para análise. Onde conseguir: URL de arquivo hospedado. Onde interfere: Arquivo será analisado para extrair informações técnicas.',
            example='https://example.com/video.mp4'
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @media_ns.doc(
        description='Extrai metadados técnicos de um arquivo de mídia. O que faz: Analisa o arquivo e retorna informações como duração, resolução, codecs, bitrate, tamanho. Onde usar: Para inspecionar propriedades de arquivos antes de processar. Processamento: Síncrono (resposta imediata).',
        body=metadata_model,
        responses={
            200: 'Metadados extraídos - retorna objeto com todas as informações técnicas',
            400: 'URL inválida ou arquivo inacessível',
            401: 'Não autorizado',
            500: 'Erro ao analisar arquivo'
        }
    )
    @media_ns.expect(metadata_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Extrai metadados de um arquivo de mídia"""
        return call_blueprint_function('v1_media_metadata.media_metadata')(self)

# Media - Silence Detection
@media_ns.route('/v1/media/silence')
@media_ns.doc(security='APIKeyHeader')
class MediaSilence(Resource):
    silence_model = media_ns.model('SilenceRequest', {
        'media_url': fields.String(
            required=True,
            description='URL pública do arquivo de mídia para análise. Onde conseguir: URL de arquivo hospedado. Onde interfere: Arquivo será analisado para detectar períodos de silêncio.',
            example='https://example.com/video.mp4'
        ),
        'duration': fields.Float(
            required=True,
            description='Duração mínima do silêncio em segundos para ser detectado. Onde conseguir: Número decimal (mínimo 0.1). Onde interfere: Valores menores detectam mais silêncios, valores maiores apenas silêncios longos. Variações: 0.5 = detecta silêncios curtos, 2.0 = apenas silêncios longos.',
            example=1.0,
            min=0.1
        ),
        'start': fields.String(
            description='Tempo de início para análise (formato hh:mm:ss.ms). Onde conseguir: String no formato "00:00:10.000". Onde interfere: Se especificado, análise começa neste ponto. Variações: Omitir = começa do início, especificar = começa do ponto indicado.',
            example='00:00:10.000'
        ),
        'end': fields.String(
            description='Tempo de fim para análise (formato hh:mm:ss.ms). Onde conseguir: String no formato "00:01:30.000". Onde interfere: Se especificado, análise termina neste ponto. Variações: Omitir = vai até o fim, especificar = termina no ponto indicado.',
            example='00:01:30.000'
        ),
        'noise': fields.String(
            description='Threshold de ruído em dB. Onde conseguir: String no formato "-NdB" (ex: "-30dB", "-25dB"). Onde interfere: Valores mais negativos = mais sensível (detecta mais silêncios). Variações: -30dB = padrão, -25dB = mais sensível, -35dB = menos sensível.',
            example='-30dB',
            default='-30dB'
        ),
        'mono': fields.Boolean(
            description='Converter áudio para mono antes de analisar. Onde conseguir: true ou false. Onde interfere: true = mais rápido e usa menos memória, false = mantém canais originais. Variações: true = recomendado, false = preserva estéreo.',
            example=True,
            default=True
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @media_ns.doc(
        description='Detecta períodos de silêncio em um arquivo de mídia. O que faz: Analisa o áudio e retorna intervalos de tempo onde há silêncio. Onde usar: Para identificar pausas, remover silêncios ou analisar padrões de áudio.',
        body=silence_model,
        responses={
            200: 'Análise concluída - retorna array com intervalos de silêncio detectados',
            202: 'Requisição enfileirada',
            400: 'Parâmetros inválidos',
            401: 'Não autorizado',
            500: 'Erro na análise'
        }
    )
    @media_ns.expect(silence_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Detecta silêncio em um arquivo de mídia"""
        return call_blueprint_function('v1_media_silence.silence')(self)

# Media - Generate ASS
@media_ns.route('/v1/media/generate/ass')
@media_ns.doc(security='APIKeyHeader')
class GenerateASS(Resource):
    ass_settings_model = media_ns.model('ASSSettings', {
        'line_color': fields.String(description='Cor da linha de legenda em hexadecimal. Onde conseguir: Código hex (ex: #FFFFFF). Onde interfere: Define cor do texto principal.', example='#FFFFFF'),
        'word_color': fields.String(description='Cor das palavras em hexadecimal. Onde conseguir: Código hex. Onde interfere: Define cor das palavras individuais (para karaoke).', example='#FFFF00'),
        'outline_color': fields.String(description='Cor da borda em hexadecimal. Onde conseguir: Código hex. Onde interfere: Define cor da borda ao redor do texto.', example='#000000'),
        'all_caps': fields.Boolean(description='Converter todo texto para maiúsculas. Onde conseguir: true/false. Onde interfere: true = texto em maiúsculas, false = mantém original.', example=False),
        'max_words_per_line': fields.Integer(description='Máximo de palavras por linha. Onde conseguir: Número inteiro. Onde interfere: Controla quebra de linhas.', example=8),
        'x': fields.Integer(description='Posição X no canvas (pixels). Onde conseguir: Número inteiro. Onde interfere: Posição horizontal do texto.', example=960),
        'y': fields.Integer(description='Posição Y no canvas (pixels). Onde conseguir: Número inteiro. Onde interfere: Posição vertical do texto.', example=900),
        'position': fields.String(
            enum=['bottom_left', 'bottom_center', 'bottom_right', 'middle_left', 'middle_center', 'middle_right', 'top_left', 'top_center', 'top_right'],
            description='Posição pré-definida no vídeo. Onde conseguir: Uma das 9 posições disponíveis. Onde interfere: Sobrescreve x e y com posição padrão. Variações: bottom_center = padrão, top_center = topo, middle_center = centro.',
            example='bottom_center'
        ),
        'alignment': fields.String(
            enum=['left', 'center', 'right'],
            description='Alinhamento do texto. Onde conseguir: left, center ou right. Onde interfere: Alinha texto dentro da posição. Variações: center = centralizado, left = esquerda, right = direita.',
            example='center'
        ),
        'font_family': fields.String(description='Família da fonte. Onde conseguir: Nome da fonte instalada (ex: Arial, Times New Roman). Onde interfere: Define fonte visual do texto.', example='Arial'),
        'font_size': fields.Integer(description='Tamanho da fonte em pixels. Onde conseguir: Número inteiro. Onde interfere: Tamanho visual do texto. Variações: 24 = padrão, 32 = grande, 18 = pequeno.', example=24),
        'bold': fields.Boolean(description='Texto em negrito. Onde conseguir: true/false. Onde interfere: true = negrito, false = normal.', example=True),
        'italic': fields.Boolean(description='Texto em itálico. Onde conseguir: true/false. Onde interfere: true = itálico, false = normal.', example=False),
        'underline': fields.Boolean(description='Texto sublinhado. Onde conseguir: true/false. Onde interfere: true = sublinhado, false = normal.', example=False),
        'strikeout': fields.Boolean(description='Texto riscado. Onde conseguir: true/false. Onde interfere: true = riscado, false = normal.', example=False),
        'style': fields.String(
            enum=['classic', 'karaoke', 'highlight', 'underline', 'word_by_word'],
            description='Estilo de animação. Onde conseguir: Um dos estilos disponíveis. Onde interfere: Define como texto aparece. Variações: classic = padrão, karaoke = destaca palavras, highlight = destaque, word_by_word = palavra por palavra.',
            example='classic'
        ),
        'outline_width': fields.Integer(description='Largura da borda em pixels. Onde conseguir: Número inteiro. Onde interfere: Espessura da borda ao redor do texto.', example=2),
        'spacing': fields.Integer(description='Espaçamento entre caracteres. Onde conseguir: Número inteiro. Onde interfere: Espaço entre letras.', example=0),
        'angle': fields.Integer(description='Ângulo de rotação do texto. Onde conseguir: Número inteiro (graus). Onde interfere: Rotaciona texto.', example=0),
        'shadow_offset': fields.Integer(description='Deslocamento da sombra em pixels. Onde conseguir: Número inteiro. Onde interfere: Posição da sombra.', example=0)
    })
    
    replace_rule_model = media_ns.model('ReplaceRule', {
        'find': fields.String(required=True, description='Texto a ser encontrado. Onde conseguir: String exata. Onde interfere: Busca este texto para substituição.', example='palavra'),
        'replace': fields.String(required=True, description='Texto de substituição. Onde conseguir: String de substituição. Onde interfere: Substitui "find" por este texto.', example='substituição')
    })
    
    time_range_model = media_ns.model('TimeRange', {
        'start': fields.String(required=True, description='Início do intervalo (hh:mm:ss.ms). Onde conseguir: Formato de tempo. Onde interfere: Define início do intervalo a excluir.', example='00:00:10.000'),
        'end': fields.String(required=True, description='Fim do intervalo (hh:mm:ss.ms). Onde conseguir: Formato de tempo. Onde interfere: Define fim do intervalo a excluir.', example='00:00:15.000')
    })
    
    generate_ass_model = media_ns.model('GenerateASSRequest', {
        'media_url': fields.String(
            required=True,
            description='URL pública do arquivo de mídia. Onde conseguir: URL de arquivo hospedado. Onde interfere: Arquivo será usado para gerar legendas ASS.',
            example='https://example.com/video.mp4'
        ),
        'canvas_width': fields.Integer(
            description='Largura do canvas em pixels (deve ser fornecido junto com canvas_height). Onde conseguir: Número inteiro (mínimo 1). Onde interfere: Define dimensões do canvas para posicionamento. Variações: 1920 = Full HD, 1280 = HD, 3840 = 4K.',
            example=1920,
            min=1
        ),
        'canvas_height': fields.Integer(
            description='Altura do canvas em pixels (deve ser fornecido junto com canvas_width). Onde conseguir: Número inteiro (mínimo 1). Onde interfere: Define dimensões do canvas para posicionamento. Variações: 1080 = Full HD, 720 = HD, 2160 = 4K.',
            example=1080,
            min=1
        ),
        'settings': fields.Nested(ass_settings_model, description='Configurações de estilo das legendas. Onde conseguir: Objeto com propriedades de estilo. Onde interfere: Controla aparência visual das legendas.'),
        'replace': fields.List(
            fields.Nested(replace_rule_model),
            description='Regras de substituição de texto. Onde conseguir: Array de objetos {find, replace}. Onde interfere: Substitui texto antes de gerar legendas. Variações: Útil para corrigir erros de transcrição.',
            example=[{'find': 'palavra', 'replace': 'substituição'}]
        ),
        'exclude_time_ranges': fields.List(
            fields.Nested(time_range_model),
            description='Intervalos de tempo a excluir das legendas. Onde conseguir: Array de objetos {start, end}. Onde interfere: Remove legendas nestes intervalos. Variações: Útil para remover legendas em silêncios ou música.',
            example=[{'start': '00:00:10.000', 'end': '00:00:15.000'}]
        ),
        'language': fields.String(
            description='Idioma para processamento. Onde conseguir: Código ISO 639-1 ou "auto". Onde interfere: Força idioma ou detecta automaticamente. Variações: pt = português, en = inglês, auto = detecta.',
            example='auto',
            default='auto'
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @media_ns.doc(
        description='Gera arquivo ASS (Advanced SubStation Alpha) para legendas com controle total sobre estilo e animação. O que faz: Cria arquivo ASS com legendas estilizadas que podem ser usadas em players de vídeo. Onde usar: Para criar legendas profissionais com animações, cores e posicionamento customizado.',
        body=generate_ass_model,
        responses={
            200: 'Arquivo ASS gerado - retorna URL do arquivo',
            202: 'Requisição enfileirada',
            400: 'Parâmetros inválidos ou fonte não encontrada',
            401: 'Não autorizado',
            500: 'Erro ao gerar ASS'
        }
    )
    @media_ns.expect(generate_ass_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Gera arquivo ASS para legendas"""
        return call_blueprint_function('v1_media_generate_ass.generate_ass_v1')(self)

# Media - Download (BETA)
@media_ns.route('/v1/BETA/media/download')
@media_ns.doc(security='APIKeyHeader')
class MediaDownload(Resource):
    format_options_model = media_ns.model('FormatOptions', {
        'quality': fields.String(description='Especificação de qualidade (ex: "best", "worst"). Onde conseguir: String de qualidade. Onde interfere: Seleciona qualidade do vídeo.', example='best'),
        'format_id': fields.String(description='ID específico do formato. Onde conseguir: ID retornado por yt-dlp. Onde interfere: Força formato específico.', example='22'),
        'resolution': fields.String(description='Resolução desejada (ex: "720p", "1080p"). Onde conseguir: String de resolução. Onde interfere: Filtra por resolução.', example='720p'),
        'video_codec': fields.String(description='Codec de vídeo preferido. Onde conseguir: Nome do codec. Onde interfere: Prefere codec específico.', example='h264'),
        'audio_codec': fields.String(description='Codec de áudio preferido. Onde conseguir: Nome do codec. Onde interfere: Prefere codec específico.', example='aac')
    })
    
    audio_options_model = media_ns.model('AudioOptions', {
        'extract': fields.Boolean(description='Extrair apenas áudio. Onde conseguir: true/false. Onde interfere: true = apenas áudio, false = vídeo completo.', example=False),
        'format': fields.String(description='Formato de áudio (ex: "mp3", "m4a"). Onde conseguir: Extensão do formato. Onde interfere: Define formato do áudio extraído.', example='mp3'),
        'quality': fields.String(description='Qualidade do áudio. Onde conseguir: String de qualidade. Onde interfere: Controla qualidade do áudio.', example='192')
    })
    
    thumbnails_options_model = media_ns.model('ThumbnailsOptions', {
        'download': fields.Boolean(description='Baixar thumbnails. Onde conseguir: true/false. Onde interfere: true = baixa thumbnails, false = não baixa.', example=True),
        'download_all': fields.Boolean(description='Baixar todas as thumbnails disponíveis. Onde conseguir: true/false. Onde interfere: true = todas, false = apenas principal.', example=False),
        'formats': fields.List(fields.String, description='Formatos de thumbnail desejados. Onde conseguir: Array de formatos (ex: ["jpg", "webp"]). Onde interfere: Filtra formatos.', example=['jpg']),
        'convert': fields.Boolean(description='Converter thumbnails. Onde conseguir: true/false. Onde interfere: true = converte, false = mantém original.', example=False),
        'embed_in_audio': fields.Boolean(description='Embutir thumbnail no arquivo de áudio. Onde conseguir: true/false. Onde interfere: true = embute, false = não embute.', example=False)
    })
    
    subtitles_options_model = media_ns.model('SubtitlesOptions', {
        'download': fields.Boolean(description='Baixar legendas. Onde conseguir: true/false. Onde interfere: true = baixa legendas, false = não baixa.', example=True),
        'languages': fields.List(fields.String, description='Idiomas das legendas. Onde conseguir: Array de códigos ISO 639-1. Onde interfere: Filtra idiomas desejados.', example=['pt', 'en']),
        'format': fields.String(
            enum=['srt', 'vtt', 'json3'],
            description='Formato das legendas. Onde conseguir: srt, vtt ou json3. Onde interfere: Define formato de saída. Variações: srt = mais comum, vtt = web, json3 = YouTube.',
            example='srt'
        ),
        'cloud_upload': fields.Boolean(description='Fazer upload das legendas para cloud. Onde conseguir: true/false. Onde interfere: true = upload, false = apenas download local.', example=True)
    })
    
    download_options_model = media_ns.model('DownloadOptions', {
        'max_filesize': fields.Integer(description='Tamanho máximo do arquivo em bytes. Onde conseguir: Número inteiro. Onde interfere: Limita tamanho do download.', example=1000000000),
        'rate_limit': fields.String(description='Limite de velocidade (ex: "5M"). Onde conseguir: String com unidade. Onde interfere: Controla velocidade de download.', example='5M'),
        'retries': fields.Integer(description='Número de tentativas em caso de falha. Onde conseguir: Número inteiro. Onde interfere: Quantas vezes tentar novamente.', example=3)
    })
    
    download_model = media_ns.model('DownloadRequest', {
        'media_url': fields.String(
            required=True,
            description='URL da mídia para download (YouTube, Vimeo, etc). Onde conseguir: URL pública de plataforma suportada. Onde interfere: URL será processada por yt-dlp para download.',
            example='https://youtube.com/watch?v=...'
        ),
        'cookie': fields.String(
            description='Cookies para autenticação (caminho, URL ou string Netscape). Onde conseguir: Arquivo de cookies exportado do navegador. Onde interfere: Permite acesso a conteúdo privado ou restrito.',
            example='cookies.txt'
        ),
        'cloud_upload': fields.Boolean(
            description='Fazer upload para cloud storage após download. Onde conseguir: true/false. Onde interfere: true = upload automático e retorna URL, false = apenas download local. Variações: true = recomendado, false = apenas local.',
            example=True,
            default=True
        ),
        'format': fields.Nested(format_options_model, description='Opções de formato do vídeo. Onde conseguir: Objeto com propriedades de formato. Onde interfere: Controla qualidade e codecs do download.'),
        'audio': fields.Nested(audio_options_model, description='Opções de extração de áudio. Onde conseguir: Objeto com propriedades de áudio. Onde interfere: Controla extração e formato do áudio.'),
        'thumbnails': fields.Nested(thumbnails_options_model, description='Opções de thumbnails. Onde conseguir: Objeto com propriedades de thumbnails. Onde interfere: Controla download e processamento de thumbnails.'),
        'subtitles': fields.Nested(subtitles_options_model, description='Opções de legendas. Onde conseguir: Objeto com propriedades de legendas. Onde interfere: Controla download e formato das legendas.'),
        'download': fields.Nested(download_options_model, description='Opções de download. Onde conseguir: Objeto com propriedades de download. Onde interfere: Controla limites e tentativas.'),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @media_ns.doc(
        description='Baixa mídia de várias plataformas usando yt-dlp (BETA). O que faz: Suporta YouTube, Vimeo, TikTok e outras plataformas. Pode extrair áudio, baixar legendas e thumbnails. Onde usar: Para baixar conteúdo de plataformas de vídeo. Requer: URL de plataforma suportada.',
        body=download_model,
        responses={
            200: 'Download concluído - retorna URL do arquivo baixado',
            202: 'Requisição enfileirada',
            400: 'URL inválida ou não suportada',
            401: 'Não autorizado',
            500: 'Erro no download'
        }
    )
    @media_ns.expect(download_model)
    @media_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Baixa mídia de URLs usando yt-dlp"""
        return call_blueprint_function('v1_media_download.download_media')(self)

# Video - Concatenate
@video_ns.route('/v1/video/concatenate')
@video_ns.doc(security='APIKeyHeader')
class ConcatenateVideos(Resource):
    concatenate_model = video_ns.model('ConcatenateRequest', {
        'video_urls': fields.List(
            fields.Nested(video_ns.model('VideoURL', {
                'video_url': fields.String(required=True, example='https://example.com/video1.mp4')
            })),
            required=True,
            description='Array de URLs dos vídeos a serem concatenados',
            min_items=1
        ),
        'webhook_url': fields.String(description='URL para receber notificação', example='https://example.com/webhook'),
        'id': fields.String(description='ID opcional', example='custom-request-id')
    })
    
    @video_ns.doc(
        description='Concatena múltiplos vídeos em um único arquivo',
        body=concatenate_model,
        responses={
            200: 'Vídeos concatenados com sucesso',
            202: 'Requisição enfileirada',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @video_ns.expect(concatenate_model)
    @video_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Concatena múltiplos vídeos em um único arquivo"""
        return call_blueprint_function('v1_video_concatenate.combine_videos')(self)

# Video - Trim
@video_ns.route('/v1/video/trim')
@video_ns.doc(security='APIKeyHeader')
class TrimVideo(Resource):
    trim_model = video_ns.model('TrimRequest', {
        'video_url': fields.String(
            required=True,
            description='URL pública do vídeo para cortar. Onde conseguir: URL de arquivo hospedado. Onde interfere: Vídeo será baixado e cortado.',
            example='https://example.com/video.mp4'
        ),
        'start': fields.String(
            required=True,
            description='Tempo de início do corte (formato hh:mm:ss.ms ou segundos). Onde conseguir: Formato de tempo (ex: "00:00:10.000" ou "10.5"). Onde interfere: Define onde o vídeo começa após o corte.',
            example='00:00:10.000'
        ),
        'end': fields.String(
            required=True,
            description='Tempo de fim do corte (formato hh:mm:ss.ms ou segundos). Onde conseguir: Formato de tempo (ex: "00:01:30.000" ou "90.5"). Onde interfere: Define onde o vídeo termina após o corte.',
            example='00:01:30.000'
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @video_ns.doc(
        description='Corta um vídeo removendo partes do início e/ou fim. O que faz: Remove segmentos do início e fim do vídeo, mantendo apenas a parte central. Onde usar: Para remover introduções, créditos ou partes indesejadas das extremidades.',
        body=trim_model,
        responses={
            200: 'Vídeo cortado - retorna URL do arquivo processado',
            202: 'Requisição enfileirada',
            400: 'Tempos inválidos ou vídeo muito curto',
            401: 'Não autorizado',
            500: 'Erro ao processar vídeo'
        }
    )
    @video_ns.expect(trim_model)
    @video_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Corta um vídeo removendo partes do início e/ou fim"""
        return call_blueprint_function('v1_video_trim.trim_video')(self)

# Video - Cut
@video_ns.route('/v1/video/cut')
@video_ns.doc(security='APIKeyHeader')
class CutVideo(Resource):
    cut_segment_model = video_ns.model('CutSegment', {
        'start': fields.String(
            required=True,
            description='Tempo de início do segmento (formato hh:mm:ss.ms). Onde conseguir: Formato de tempo. Onde interfere: Define início do segmento a manter.',
            example='00:00:10.000'
        ),
        'end': fields.String(
            required=True,
            description='Tempo de fim do segmento (formato hh:mm:ss.ms). Onde conseguir: Formato de tempo. Onde interfere: Define fim do segmento a manter.',
            example='00:00:20.000'
        )
    })
    
    cut_model = video_ns.model('CutRequest', {
        'video_url': fields.String(
            required=True,
            description='URL pública do vídeo para cortar. Onde conseguir: URL de arquivo hospedado. Onde interfere: Vídeo será baixado e processado.',
            example='https://example.com/video.mp4'
        ),
        'segments': fields.List(
            fields.Nested(cut_segment_model),
            required=True,
            description='Array de segmentos a manter no vídeo. Onde conseguir: Array de objetos {start, end}. Onde interfere: Define quais partes do vídeo serão mantidas. Variações: Múltiplos segmentos = mantém várias partes, um segmento = mantém uma parte.',
            min_items=1
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @video_ns.doc(
        description='Corta um vídeo mantendo apenas segmentos específicos. O que faz: Remove tudo exceto os segmentos especificados, concatenando-os em ordem. Onde usar: Para extrair múltiplas cenas de um vídeo longo, removendo partes indesejadas.',
        body=cut_model,
        responses={
            200: 'Vídeo cortado - retorna URL do arquivo processado',
            202: 'Requisição enfileirada',
            400: 'Segmentos inválidos ou sobrepostos',
            401: 'Não autorizado',
            500: 'Erro ao processar vídeo'
        }
    )
    @video_ns.expect(cut_model)
    @video_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Corta um vídeo mantendo apenas segmentos específicos"""
        return call_blueprint_function('v1_video_cut.cut_video')(self)

# Video - Split
@video_ns.route('/v1/video/split')
@video_ns.doc(security='APIKeyHeader')
class SplitVideo(Resource):
    split_model = video_ns.model('SplitRequest', {
        'video_url': fields.String(
            required=True,
            description='URL pública do vídeo para dividir. Onde conseguir: URL de arquivo hospedado. Onde interfere: Vídeo será baixado e dividido.',
            example='https://example.com/video.mp4'
        ),
        'duration': fields.String(
            required=True,
            description='Duração de cada segmento (formato hh:mm:ss.ms ou segundos). Onde conseguir: Formato de tempo (ex: "00:05:00.000" ou "300"). Onde interfere: Define tamanho de cada parte. Variações: 5 minutos = partes de 5min, 1 minuto = partes de 1min.',
            example='00:05:00.000'
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @video_ns.doc(
        description='Divide um vídeo em múltiplos segmentos de duração igual. O que faz: Corta o vídeo em partes menores de duração especificada. Onde usar: Para dividir vídeos longos em partes menores para facilitar upload ou processamento.',
        body=split_model,
        responses={
            200: 'Vídeo dividido - retorna array de URLs dos segmentos',
            202: 'Requisição enfileirada',
            400: 'Duração inválida ou vídeo muito curto',
            401: 'Não autorizado',
            500: 'Erro ao processar vídeo'
        }
    )
    @video_ns.expect(split_model)
    @video_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Divide um vídeo em múltiplos segmentos"""
        return call_blueprint_function('v1_video_split.split_video')(self)

# Video - Thumbnail
@video_ns.route('/v1/video/thumbnail')
@video_ns.doc(security='APIKeyHeader')
class VideoThumbnail(Resource):
    thumbnail_model = video_ns.model('ThumbnailRequest', {
        'video_url': fields.String(
            required=True,
            description='URL pública do vídeo para extrair thumbnail. Onde conseguir: URL de arquivo hospedado. Onde interfere: Vídeo será analisado para extrair frame.',
            example='https://example.com/video.mp4'
        ),
        'time': fields.String(
            description='Tempo para extrair o frame (formato hh:mm:ss.ms ou segundos). Onde conseguir: Formato de tempo (ex: "00:00:10.000" ou "10.5"). Onde interfere: Define qual frame será extraído. Variações: Omitir = frame do meio, especificar = frame no tempo indicado.',
            example='00:00:10.000'
        ),
        'width': fields.Integer(
            description='Largura da thumbnail em pixels. Onde conseguir: Número inteiro. Onde interfere: Redimensiona largura mantendo proporção. Variações: Omitir = largura original, especificar = redimensiona.',
            example=1280,
            min=1
        ),
        'height': fields.Integer(
            description='Altura da thumbnail em pixels. Onde conseguir: Número inteiro. Onde interfere: Redimensiona altura mantendo proporção. Variações: Omitir = altura original, especificar = redimensiona.',
            example=720,
            min=1
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @video_ns.doc(
        description='Extrai uma thumbnail (frame) de um vídeo. O que faz: Captura um frame específico do vídeo e retorna como imagem. Onde usar: Para gerar previews, capas ou thumbnails de vídeos. Processamento: Síncrono (resposta imediata).',
        body=thumbnail_model,
        responses={
            200: 'Thumbnail extraída - retorna URL da imagem',
            400: 'Tempo inválido ou vídeo inacessível',
            401: 'Não autorizado',
            500: 'Erro ao extrair thumbnail'
        }
    )
    @video_ns.expect(thumbnail_model)
    @video_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Extrai uma thumbnail de um vídeo"""
        return call_blueprint_function('v1_video_thumbnail.video_thumbnail')(self)

# Video - Caption
@video_ns.route('/v1/video/caption')
@video_ns.doc(security='APIKeyHeader')
class CaptionVideo(Resource):
    caption_position_model = video_ns.model('CaptionPosition', {
        'x': fields.Integer(description='Posição X em pixels. Onde conseguir: Número inteiro. Onde interfere: Posição horizontal do texto.', example=960),
        'y': fields.Integer(description='Posição Y em pixels. Onde conseguir: Número inteiro. Onde interfere: Posição vertical do texto.', example=900),
        'position': fields.String(
            enum=['bottom_left', 'bottom_center', 'bottom_right', 'middle_left', 'middle_center', 'middle_right', 'top_left', 'top_center', 'top_right'],
            description='Posição pré-definida. Onde conseguir: Uma das 9 posições. Onde interfere: Sobrescreve x e y. Variações: bottom_center = padrão, top_center = topo.',
            example='bottom_center'
        )
    })
    
    caption_style_model = video_ns.model('CaptionStyle', {
        'font_family': fields.String(description='Família da fonte. Onde conseguir: Nome da fonte. Onde interfere: Define fonte visual.', example='Arial'),
        'font_size': fields.Integer(description='Tamanho da fonte. Onde conseguir: Número inteiro. Onde interfere: Tamanho visual do texto.', example=24),
        'font_color': fields.String(description='Cor da fonte (hex). Onde conseguir: Código hex. Onde interfere: Cor do texto.', example='#FFFFFF'),
        'background_color': fields.String(description='Cor de fundo (hex). Onde conseguir: Código hex. Onde interfere: Cor do fundo do texto.', example='#000000'),
        'background_opacity': fields.Float(description='Opacidade do fundo (0-1). Onde conseguir: Decimal. Onde interfere: Transparência do fundo.', example=0.7, min=0, max=1),
        'outline_color': fields.String(description='Cor da borda (hex). Onde conseguir: Código hex. Onde interfere: Cor da borda.', example='#000000'),
        'outline_width': fields.Integer(description='Largura da borda. Onde conseguir: Número inteiro. Onde interfere: Espessura da borda.', example=2),
        'alignment': fields.String(
            enum=['left', 'center', 'right'],
            description='Alinhamento. Onde conseguir: left, center ou right. Onde interfere: Alinha texto. Variações: center = centralizado.',
            example='center'
        ),
        'bold': fields.Boolean(description='Negrito. Onde conseguir: true/false. Onde interfere: true = negrito.', example=True),
        'italic': fields.Boolean(description='Itálico. Onde conseguir: true/false. Onde interfere: true = itálico.', example=False)
    })
    
    caption_model = video_ns.model('CaptionRequest', {
        'video_url': fields.String(
            required=True,
            description='URL pública do vídeo para adicionar legendas. Onde conseguir: URL de arquivo hospedado. Onde interfere: Vídeo será processado com legendas embutidas.',
            example='https://example.com/video.mp4'
        ),
        'subtitles_url': fields.String(
            required=True,
            description='URL pública do arquivo de legendas (SRT, VTT, ASS). Onde conseguir: URL de arquivo de legendas hospedado. Onde interfere: Legendas serão embutidas no vídeo.',
            example='https://example.com/subtitles.srt'
        ),
        'position': fields.Nested(caption_position_model, description='Posição das legendas. Onde conseguir: Objeto com x, y ou position. Onde interfere: Onde legendas aparecem no vídeo.'),
        'style': fields.Nested(caption_style_model, description='Estilo das legendas. Onde conseguir: Objeto com propriedades de estilo. Onde interfere: Aparência visual das legendas.'),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @video_ns.doc(
        description='Adiciona legendas embutidas a um vídeo. O que faz: Queima legendas no vídeo de forma permanente. Onde usar: Para criar vídeos com legendas fixas que não podem ser desativadas.',
        body=caption_model,
        responses={
            200: 'Legendas adicionadas - retorna URL do vídeo com legendas',
            202: 'Requisição enfileirada',
            400: 'Arquivo de legendas inválido ou formato não suportado',
            401: 'Não autorizado',
            500: 'Erro ao processar vídeo'
        }
    )
    @video_ns.expect(caption_model)
    @video_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Adiciona legendas embutidas a um vídeo"""
        return call_blueprint_function('v1_video/caption.caption_video_v1')(self)

# Audio - Concatenate
@audio_ns.route('/v1/audio/concatenate')
@audio_ns.doc(security='APIKeyHeader')
class ConcatenateAudio(Resource):
    concatenate_model = audio_ns.model('ConcatenateAudioRequest', {
        'audio_urls': fields.List(
            fields.Nested(audio_ns.model('AudioURL', {
                'audio_url': fields.String(required=True, example='https://example.com/audio1.mp3')
            })),
            required=True,
            description='Array de URLs dos arquivos de áudio a serem concatenados',
            min_items=1
        ),
        'webhook_url': fields.String(description='URL para receber notificação', example='https://example.com/webhook'),
        'id': fields.String(description='ID opcional', example='custom-request-id')
    })
    
    @audio_ns.doc(
        description='Concatena múltiplos arquivos de áudio em um único arquivo',
        body=concatenate_model,
        responses={
            200: 'Áudios concatenados com sucesso',
            202: 'Requisição enfileirada',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @audio_ns.expect(concatenate_model)
    @audio_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Concatena múltiplos arquivos de áudio em um único arquivo"""
        return call_blueprint_function('v1_audio_concatenate.combine_audio')(self)

# S3 - Upload
@s3_ns.route('/v1/s3/upload')
@s3_ns.doc(security='APIKeyHeader')
class S3Upload(Resource):
    upload_model = s3_ns.model('S3UploadRequest', {
        'file_url': fields.String(required=True, description='URL do arquivo para fazer upload', example='https://example.com/file.mp4'),
        'filename': fields.String(description='Nome do arquivo no S3', example='my-file.mp4'),
        'public': fields.Boolean(description='Tornar arquivo público', example=False),
        'webhook_url': fields.String(description='URL para receber notificação', example='https://example.com/webhook'),
        'id': fields.String(description='ID opcional', example='custom-request-id')
    })
    
    @s3_ns.doc(
        description='Faz upload de um arquivo para S3 via streaming direto da URL',
        body=upload_model,
        responses={
            200: 'Upload concluído com sucesso',
            202: 'Requisição enfileirada',
            400: 'Requisição inválida',
            401: 'Não autorizado',
            500: 'Erro interno do servidor'
        }
    )
    @s3_ns.expect(upload_model)
    @s3_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Faz upload de um arquivo para S3 via streaming direto da URL"""
        return call_blueprint_function('v1_s3_upload.s3_upload_endpoint')(self)

# Image - Convert to Video
@image_ns.route('/v1/image/convert/video')
@image_ns.doc(security='APIKeyHeader')
class ImageToVideo(Resource):
    image_to_video_model = image_ns.model('ImageToVideoRequest', {
        'image_url': fields.String(
            required=True,
            description='URL pública da imagem para converter. Onde conseguir: URL de imagem hospedada. Onde interfere: Imagem será usada para criar vídeo.',
            example='https://example.com/image.jpg'
        ),
        'duration': fields.String(
            required=True,
            description='Duração do vídeo (formato hh:mm:ss.ms ou segundos). Onde conseguir: Formato de tempo (ex: "00:00:05.000" ou "5"). Onde interfere: Define duração do vídeo gerado. Variações: 5 segundos = vídeo curto, 30 segundos = vídeo longo.',
            example='00:00:05.000'
        ),
        'fps': fields.Integer(
            description='Frames por segundo do vídeo. Onde conseguir: Número inteiro (mínimo 1, máximo 60). Onde interfere: Controla suavidade do vídeo. Variações: 24 = cinema, 30 = padrão, 60 = muito suave.',
            example=30,
            default=30,
            min=1,
            max=60
        ),
        'width': fields.Integer(
            description='Largura do vídeo em pixels. Onde conseguir: Número inteiro. Onde interfere: Redimensiona largura. Variações: Omitir = largura da imagem, especificar = redimensiona.',
            example=1920,
            min=1
        ),
        'height': fields.Integer(
            description='Altura do vídeo em pixels. Onde conseguir: Número inteiro. Onde interfere: Redimensiona altura. Variações: Omitir = altura da imagem, especificar = redimensiona.',
            example=1080,
            min=1
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @image_ns.doc(
        description='Converte uma imagem estática em um vídeo. O que faz: Cria um vídeo mostrando a imagem por uma duração especificada. Onde usar: Para criar vídeos a partir de imagens, slides ou thumbnails.',
        body=image_to_video_model,
        responses={
            200: 'Vídeo gerado - retorna URL do arquivo',
            202: 'Requisição enfileirada',
            400: 'Imagem inválida ou parâmetros incorretos',
            401: 'Não autorizado',
            500: 'Erro ao gerar vídeo'
        }
    )
    @image_ns.expect(image_to_video_model)
    @image_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Converte uma imagem em vídeo"""
        return call_blueprint_function('v1_image_convert_video.image_to_video')(self)

# Image - Screenshot Webpage
@image_ns.route('/v1/image/screenshot/webpage')
@image_ns.doc(security='APIKeyHeader')
class ScreenshotWebpage(Resource):
    screenshot_model = image_ns.model('ScreenshotRequest', {
        'url': fields.String(
            required=True,
            description='URL da página web para capturar. Onde conseguir: URL pública de qualquer site. Onde interfere: Página será carregada e capturada como imagem.',
            example='https://example.com'
        ),
        'width': fields.Integer(
            description='Largura da viewport em pixels. Onde conseguir: Número inteiro (mínimo 1). Onde interfere: Define largura da captura. Variações: 1920 = desktop, 1280 = tablet, 375 = mobile.',
            example=1920,
            default=1920,
            min=1
        ),
        'height': fields.Integer(
            description='Altura da viewport em pixels. Onde conseguir: Número inteiro (mínimo 1). Onde interfere: Define altura da captura. Variações: 1080 = desktop, 720 = tablet, 667 = mobile.',
            example=1080,
            default=1080,
            min=1
        ),
        'full_page': fields.Boolean(
            description='Capturar página completa (scroll). Onde conseguir: true ou false. Onde interfere: true = captura toda página, false = apenas viewport visível. Variações: true = página completa, false = apenas visível.',
            example=True,
            default=True
        ),
        'wait': fields.Integer(
            description='Tempo de espera antes de capturar em milissegundos. Onde conseguir: Número inteiro (mínimo 0). Onde interfere: Aguarda este tempo para carregar conteúdo dinâmico. Variações: 0 = imediato, 2000 = 2 segundos, 5000 = 5 segundos.',
            example=2000,
            default=2000,
            min=0
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @image_ns.doc(
        description='Captura screenshot de uma página web. O que faz: Usa Playwright para carregar e capturar página como imagem. Onde usar: Para gerar previews de sites, documentação ou testes visuais. Processamento: Síncrono (resposta imediata).',
        body=screenshot_model,
        responses={
            200: 'Screenshot capturado - retorna URL da imagem',
            400: 'URL inválida ou página inacessível',
            401: 'Não autorizado',
            500: 'Erro ao capturar screenshot'
        }
    )
    @image_ns.expect(screenshot_model)
    @image_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Captura screenshot de uma página web"""
        return call_blueprint_function('v1_image_screenshot_webpage.screenshot_webpage')(self)

# GCP - Upload
@gcp_ns.route('/v1/gcp/upload')
@gcp_ns.doc(security='APIKeyHeader')
class GCPUpload(Resource):
    gcp_upload_model = gcp_ns.model('GCPUploadRequest', {
        'file_url': fields.String(
            required=True,
            description='URL do arquivo para fazer upload. Onde conseguir: URL pública de arquivo hospedado. Onde interfere: Arquivo será baixado e enviado para GCS.',
            example='https://example.com/file.mp4'
        ),
        'bucket_name': fields.String(
            required=True,
            description='Nome do bucket GCS de destino. Onde conseguir: Nome do bucket criado no Google Cloud Storage. Onde interfere: Define onde arquivo será armazenado.',
            example='my-bucket'
        ),
        'object_name': fields.String(
            description='Nome do objeto no bucket (caminho completo). Onde conseguir: Caminho dentro do bucket (ex: "videos/my-file.mp4"). Onde interfere: Define nome e localização no bucket. Variações: Omitir = usa nome original, especificar = nome customizado.',
            example='videos/my-file.mp4'
        ),
        'public': fields.Boolean(
            description='Tornar arquivo público. Onde conseguir: true ou false. Onde interfere: true = acesso público, false = acesso privado. Variações: true = qualquer um pode acessar, false = apenas com credenciais.',
            example=False,
            default=False
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @gcp_ns.doc(
        description='Faz upload de um arquivo para Google Cloud Storage via streaming direto da URL. O que faz: Baixa arquivo da URL e faz upload direto para GCS sem armazenar localmente. Onde usar: Para fazer upload de arquivos grandes para GCS de forma eficiente. Requer: Credenciais GCP configuradas e bucket existente.',
        body=gcp_upload_model,
        responses={
            200: 'Upload concluído - retorna URL do arquivo no GCS',
            202: 'Requisição enfileirada',
            400: 'Bucket não encontrado ou credenciais inválidas',
            401: 'Não autorizado',
            500: 'Erro no upload'
        }
    )
    @gcp_ns.expect(gcp_upload_model)
    @gcp_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Faz upload de um arquivo para Google Cloud Storage"""
        return call_blueprint_function('v1_gcp_upload.gcp_upload_endpoint')(self)

# Code - Execute Python
@code_ns.route('/v1/code/execute/python')
@code_ns.doc(security='APIKeyHeader')
class ExecutePython(Resource):
    execute_python_model = code_ns.model('ExecutePythonRequest', {
        'code': fields.String(
            required=True,
            description='Código Python para executar. Onde conseguir: String com código Python válido. Onde interfere: Código será executado em ambiente isolado. Requer: Código Python válido e seguro.',
            example='print("Hello, World!")'
        ),
        'timeout': fields.Integer(
            description='Timeout em segundos. Onde conseguir: Número inteiro (mínimo 1, máximo 300). Onde interfere: Tempo máximo de execução. Variações: 10 = rápido, 60 = padrão, 300 = longo.',
            example=60,
            default=60,
            min=1,
            max=300
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @code_ns.doc(
        description='Executa código Python em ambiente isolado. O que faz: Roda código Python fornecido e retorna stdout, stderr e código de saída. Onde usar: Para executar scripts Python customizados, processar dados ou fazer cálculos. Requer: Código Python válido. Limitações: Sem acesso a rede, sistema de arquivos limitado, timeout configurável.',
        body=execute_python_model,
        responses={
            200: 'Código executado - retorna stdout, stderr e exit_code',
            202: 'Requisição enfileirada',
            400: 'Código inválido ou timeout',
            401: 'Não autorizado',
            500: 'Erro na execução'
        }
    )
    @code_ns.expect(execute_python_model)
    @code_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Executa código Python em ambiente isolado"""
        return call_blueprint_function('v1_code_execute_python.execute_python')(self)

# FFmpeg - Compose
@ffmpeg_ns.route('/v1/ffmpeg/compose')
@ffmpeg_ns.doc(security='APIKeyHeader')
class FFmpegCompose(Resource):
    # Modelos aninhados para FFmpeg Compose
    ffmpeg_option_model = ffmpeg_ns.model('FFmpegOption', {
        'option': fields.String(
            required=True,
            description='Nome da opção FFmpeg (ex: "-c:v", "-crf", "-ss"). Onde conseguir: Nome da opção FFmpeg. Onde interfere: Define qual opção será aplicada.',
            example='-c:v'
        ),
        'argument': fields.Raw(
            description='Argumento da opção (string, número ou null). Onde conseguir: Valor correspondente à opção. Onde interfere: Define valor da opção. Variações: String para codecs, número para valores numéricos, null para flags sem argumento.',
            example='libx264'
        )
    })
    
    ffmpeg_input_model = ffmpeg_ns.model('FFmpegInput', {
        'file_url': fields.String(
            required=True,
            description='URL pública do arquivo de entrada. Onde conseguir: URL de arquivo hospedado publicamente. Onde interfere: Arquivo será baixado e usado como entrada.',
            example='https://example.com/video.mp4'
        ),
        'options': fields.List(
            fields.Nested(ffmpeg_option_model),
            description='Opções FFmpeg para o arquivo de entrada (ex: "-ss" para início, "-t" para duração). Onde conseguir: Array de objetos {option, argument}. Onde interfere: Aplica opções antes de processar o arquivo. Exemplos: [{"option": "-ss", "argument": 10}] para começar em 10s.',
            example=[{'option': '-ss', 'argument': 10}]
        )
    })
    
    ffmpeg_filter_model = ffmpeg_ns.model('FFmpegFilter', {
        'filter': fields.String(
            required=True,
            description='Filtro FFmpeg completo (ex: "scale=1280:720", "drawtext=text=\'Hello\':fontsize=24"). Onde conseguir: String com sintaxe de filtro FFmpeg. Onde interfere: Aplica transformações ao vídeo/áudio. Exemplos: "hflip" para espelhar, "drawtext=text=\'Olá 😎\':fontfile=/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf:fontsize=48" para texto com emoji. Nota: Para emojis coloridos, use filtro "subtitles" com arquivo ASS.',
            example='drawtext=text=\'Olá 😎\':fontfile=/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf:fontsize=48:x=100:y=100'
        )
    })
    
    ffmpeg_output_model = ffmpeg_ns.model('FFmpegOutput', {
        'options': fields.List(
            fields.Nested(ffmpeg_option_model),
            required=True,
            description='Opções FFmpeg para o arquivo de saída (codecs, qualidade, formato). Onde conseguir: Array de objetos {option, argument}. Onde interfere: Define formato e qualidade do arquivo de saída. Exemplos: [{"option": "-c:v", "argument": "libx264"}, {"option": "-crf", "argument": 23}].',
            example=[{'option': '-c:v', 'argument': 'libx264'}, {'option': '-crf', 'argument': 23}]
        )
    })
    
    ffmpeg_metadata_model = ffmpeg_ns.model('FFmpegMetadata', {
        'thumbnail': fields.Boolean(
            description='Incluir thumbnail na resposta. Onde conseguir: true/false. Onde interfere: Se true, gera e retorna URL do thumbnail.',
            example=True
        ),
        'filesize': fields.Boolean(
            description='Incluir tamanho do arquivo na resposta. Onde conseguir: true/false. Onde interfere: Se true, retorna tamanho em bytes.',
            example=True
        ),
        'duration': fields.Boolean(
            description='Incluir duração na resposta. Onde conseguir: true/false. Onde interfere: Se true, retorna duração em segundos.',
            example=True
        ),
        'bitrate': fields.Boolean(
            description='Incluir bitrate na resposta. Onde conseguir: true/false. Onde interfere: Se true, retorna bitrate em bits/segundo.',
            example=True
        ),
        'encoder': fields.Boolean(
            description='Incluir codecs usados na resposta. Onde conseguir: true/false. Onde interfere: Se true, retorna codecs de vídeo e áudio.',
            example=True
        )
    })
    
    ffmpeg_compose_model = ffmpeg_ns.model('FFmpegComposeRequest', {
        'inputs': fields.List(
            fields.Nested(ffmpeg_input_model),
            required=True,
            description='Array de arquivos de entrada. Onde conseguir: Array de objetos com file_url e opções opcionais. Onde interfere: Define quais arquivos serão processados. Mínimo: 1 arquivo.',
            example=[{'file_url': 'https://example.com/video.mp4'}]
        ),
        'filters': fields.List(
            fields.Nested(ffmpeg_filter_model),
            description='Array de filtros FFmpeg a aplicar. Onde conseguir: Array de objetos com filter. Onde interfere: Aplica transformações (redimensionar, texto, efeitos). Exemplos: [{"filter": "scale=1280:720"}], [{"filter": "drawtext=text=\'Olá 😎\':fontfile=/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf:fontsize=48"}]. Nota: Para emojis coloridos, use "subtitles" com arquivo ASS hospedado.',
            example=[{'filter': 'scale=1280:720'}]
        ),
        'outputs': fields.List(
            fields.Nested(ffmpeg_output_model),
            required=True,
            description='Array de configurações de saída. Onde conseguir: Array de objetos com options. Onde interfere: Define formato e qualidade dos arquivos gerados. Mínimo: 1 saída.',
            example=[{'options': [{'option': '-c:v', 'argument': 'libx264'}, {'option': '-crf', 'argument': 23}]}]
        ),
        'global_options': fields.List(
            fields.Nested(ffmpeg_option_model),
            description='Opções globais FFmpeg (aplicadas antes dos inputs). Onde conseguir: Array de objetos {option, argument}. Onde interfere: Aplica opções globais como "-y" para sobrescrever arquivos.',
            example=[{'option': '-y'}]
        ),
        'metadata': fields.Nested(
            ffmpeg_metadata_model,
            description='Metadados a incluir na resposta. Onde conseguir: Objeto com flags booleanas. Onde interfere: Define quais informações extras serão retornadas.',
            example={'thumbnail': True, 'filesize': True}
        ),
        'webhook_url': webhook_url_field,
        'id': id_field
    })
    
    @ffmpeg_ns.doc(
        description='Interface flexível para compor comandos FFmpeg complexos. O que faz: Permite construir qualquer operação FFmpeg com controle total sobre inputs, filtros e outputs. Onde usar: Para operações avançadas não cobertas por outros endpoints. Requer: Conhecimento de sintaxe FFmpeg. Exemplos: Redimensionar vídeo (scale), adicionar texto com emojis (drawtext), aplicar efeitos (hflip, vflip), conversões avançadas. Suporte a emojis: Use fontfile=/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf no drawtext (Docker) ou fonte instalada localmente (macOS). Para emojis coloridos, use filtro "subtitles" com arquivo ASS. Veja FONTES_EMOJI.md para detalhes de instalação.',
        body=ffmpeg_compose_model,
        responses={
            200: 'Processamento concluído - retorna URL do arquivo processado',
            202: 'Requisição enfileirada',
            400: 'Payload inválido ou parâmetros incorretos',
            401: 'Não autorizado',
            500: 'Erro ao executar FFmpeg'
        }
    )
    @ffmpeg_ns.expect(ffmpeg_compose_model)
    @ffmpeg_ns.marshal_with(success_response_model, code=200)
    def post(self):
        """Executa comando FFmpeg customizado com estrutura flexível"""
        return call_blueprint_function('v1_ffmpeg_compose.ffmpeg_compose')(self)

# Função para registrar todos os namespaces na API
def register_restx_namespaces(api):
    """Registra todos os namespaces na API Flask-RESTX"""
    api.add_namespace(toolkit_ns)
    api.add_namespace(video_ns)
    api.add_namespace(audio_ns)
    api.add_namespace(media_ns)
    api.add_namespace(s3_ns)
    api.add_namespace(image_ns)
    api.add_namespace(gcp_ns)
    api.add_namespace(ffmpeg_ns)
    api.add_namespace(code_ns)

