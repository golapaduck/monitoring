"""프로그램 메트릭 조회 API."""

from flask import Blueprint, jsonify, session, request
from utils.database import get_resource_usage
from utils.cache import get_cache
import logging

logger = logging.getLogger(__name__)

metrics_api = Blueprint('metrics_api', __name__, url_prefix='/api/metrics')


@metrics_api.route('/<int:program_id>', methods=['GET'])
def get_program_metrics(program_id):
    """프로그램의 리소스 사용량 기록 조회 (캐싱 적용).
    
    Args:
        program_id: 프로그램 ID
        
    Query Parameters:
        hours: 조회할 시간 범위 (기본: 24시간, 최대: 168시간)
        
    Returns:
        JSON: {
            "metrics": [
                {
                    "id": 1,
                    "program_id": 1,
                    "cpu_percent": 15.5,
                    "memory_mb": 128.3,
                    "timestamp": "2024-01-01 12:00:00"
                },
                ...
            ]
        }
    """
    # 인증 확인
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    hours = request.args.get('hours', default=24, type=int)
    
    # 최대 7일(168시간)로 제한
    if hours > 168:
        hours = 168
    
    try:
        # 캐시 키 생성 (프로그램 ID + 시간 범위)
        cache_key = f"metrics:{program_id}:{hours}"
        
        # 캐시 확인 (5분 TTL)
        cache = get_cache()
        cached_metrics = cache.get(cache_key)
        if cached_metrics is not None:
            logger.debug(f"메트릭 캐시 히트: program_id={program_id}, hours={hours}")
            return jsonify({"metrics": cached_metrics}), 200
        
        # DB에서 조회
        metrics = get_resource_usage(program_id, hours=hours)
        
        # 캐시에 저장 (5분)
        cache.set(cache_key, metrics)
        logger.debug(f"메트릭 캐시 저장: program_id={program_id}, hours={hours}, count={len(metrics)}")
        
        return jsonify({"metrics": metrics}), 200
    except Exception as e:
        logger.error(f"메트릭 조회 오류: {str(e)}")
        return jsonify({"error": str(e)}), 500
