"""Prometheus 메트릭 수집 유틸리티.

API 응답 시간, 요청 수, 에러율 등을 Prometheus 형식으로 수집합니다.
매우 가볍고 효율적입니다.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 메트릭 정의 (Prometheus 형식)
# ============================================================================

# 1. 요청 카운터 (총 요청 수)
http_requests_total = Counter(
    'http_requests_total',
    '총 HTTP 요청 수',
    ['method', 'endpoint', 'status']
)

# 2. 요청 지연 시간 (히스토그램)
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP 요청 지연 시간 (초)',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)  # 0.01초 ~ 10초
)

# 3. 활성 연결 수 (게이지)
websocket_connections_active = Gauge(
    'websocket_connections_active',
    '활성 WebSocket 연결 수'
)

# 4. 프로세스 상태 변화 (카운터)
process_status_changes_total = Counter(
    'process_status_changes_total',
    '프로세스 상태 변화 총 수',
    ['program_name', 'status']
)

# 5. 데이터베이스 쿼리 시간 (히스토그램)
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    '데이터베이스 쿼리 지연 시간 (초)',
    ['query_type'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
)

# 6. 캐시 히트율 (카운터)
cache_hits_total = Counter(
    'cache_hits_total',
    '캐시 히트 총 수',
    ['cache_key']
)

cache_misses_total = Counter(
    'cache_misses_total',
    '캐시 미스 총 수',
    ['cache_key']
)

# 7. 에러 수 (카운터)
errors_total = Counter(
    'errors_total',
    '총 에러 수',
    ['error_type', 'endpoint']
)

# 8. 메트릭 수집 시간 (히스토그램)
metrics_collection_duration_seconds = Histogram(
    'metrics_collection_duration_seconds',
    '메트릭 수집 지연 시간 (초)',
    ['program_id'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0)
)

# 9. 시스템 리소스 (게이지)
system_memory_usage_bytes = Gauge(
    'system_memory_usage_bytes',
    '시스템 메모리 사용량 (바이트)'
)

system_cpu_usage_percent = Gauge(
    'system_cpu_usage_percent',
    '시스템 CPU 사용률 (%)'
)

# ============================================================================
# 메트릭 기록 함수
# ============================================================================

def record_http_request(method, endpoint, status, duration):
    """HTTP 요청 메트릭 기록.
    
    Args:
        method: HTTP 메서드 (GET, POST 등)
        endpoint: 엔드포인트 경로
        status: HTTP 상태 코드
        duration: 요청 지연 시간 (초)
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_websocket_connection(connected):
    """WebSocket 연결 상태 기록.
    
    Args:
        connected: True (연결), False (연결 해제)
    """
    if connected:
        websocket_connections_active.inc()
    else:
        websocket_connections_active.dec()


def record_process_status_change(program_name, status):
    """프로세스 상태 변화 기록.
    
    Args:
        program_name: 프로그램 이름
        status: 상태 (running, stopped, crashed)
    """
    process_status_changes_total.labels(program_name=program_name, status=status).inc()


def record_db_query(query_type, duration):
    """데이터베이스 쿼리 메트릭 기록.
    
    Args:
        query_type: 쿼리 타입 (select, insert, update, delete)
        duration: 쿼리 지연 시간 (초)
    """
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)


def record_cache_hit(cache_key):
    """캐시 히트 기록.
    
    Args:
        cache_key: 캐시 키
    """
    cache_hits_total.labels(cache_key=cache_key).inc()


def record_cache_miss(cache_key):
    """캐시 미스 기록.
    
    Args:
        cache_key: 캐시 키
    """
    cache_misses_total.labels(cache_key=cache_key).inc()


def record_error(error_type, endpoint):
    """에러 기록.
    
    Args:
        error_type: 에러 타입 (validation_error, database_error, etc)
        endpoint: 엔드포인트 경로
    """
    errors_total.labels(error_type=error_type, endpoint=endpoint).inc()


def record_metrics_collection(program_id, duration):
    """메트릭 수집 시간 기록.
    
    Args:
        program_id: 프로그램 ID
        duration: 수집 지연 시간 (초)
    """
    metrics_collection_duration_seconds.labels(program_id=program_id).observe(duration)


def update_system_metrics(memory_bytes, cpu_percent):
    """시스템 리소스 메트릭 업데이트.
    
    Args:
        memory_bytes: 메모리 사용량 (바이트)
        cpu_percent: CPU 사용률 (%)
    """
    system_memory_usage_bytes.set(memory_bytes)
    system_cpu_usage_percent.set(cpu_percent)


def get_metrics():
    """Prometheus 형식의 메트릭 반환.
    
    Returns:
        bytes: Prometheus 형식의 메트릭
    """
    return generate_latest()


# ============================================================================
# Flask 통합
# ============================================================================

def init_prometheus(app):
    """Prometheus 메트릭 엔드포인트 등록.
    
    Args:
        app: Flask 애플리케이션 인스턴스
    """
    @app.route('/metrics', methods=['GET'])
    def metrics():
        """Prometheus 메트릭 엔드포인트.
        
        Returns:
            Prometheus 형식의 메트릭
        """
        return get_metrics(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    logger.info("Prometheus 메트릭 엔드포인트 등록: /metrics")


def prometheus_middleware(app):
    """Flask 요청 메트릭 자동 기록 미들웨어.
    
    Args:
        app: Flask 애플리케이션 인스턴스
    """
    @app.before_request
    def before_request():
        """요청 시작 시간 기록."""
        from flask import request
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """요청 완료 후 메트릭 기록."""
        from flask import request
        
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            endpoint = request.endpoint or 'unknown'
            
            # /metrics 엔드포인트는 제외 (무한 루프 방지)
            if endpoint != 'metrics':
                record_http_request(
                    method=request.method,
                    endpoint=endpoint,
                    status=response.status_code,
                    duration=duration
                )
        
        return response
