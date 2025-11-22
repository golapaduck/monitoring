"""Rate Limiting 유틸리티.

API 요청 속도 제한을 통해 서버 보호 및 공정한 리소스 사용을 보장합니다.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

# 글로벌 Rate Limiter 인스턴스
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # 메모리 기반 저장소
)


def init_limiter(app):
    """Rate Limiter 초기화.
    
    Args:
        app: Flask 애플리케이션 인스턴스
    """
    limiter.init_app(app)
    logger.info("Rate Limiter 초기화 완료")
    return limiter


# Rate Limiting 정책 정의
RATE_LIMITS = {
    # 인증 API (엄격함)
    "auth": "5 per minute",  # 로그인 시도 제한
    
    # 프로그램 관리 API (중간)
    "programs_list": "30 per minute",
    "programs_detail": "60 per minute",
    "programs_action": "10 per minute",  # 시작/종료/재시작
    
    # 메트릭 조회 (관대함)
    "metrics": "100 per minute",
    
    # 플러그인 API (중간)
    "plugins": "30 per minute",
    
    # 웹훅 API (관대함)
    "webhook": "100 per minute",
    
    # 파일 탐색 (중간)
    "file_explorer": "30 per minute",
    
    # 작업 큐 (중간)
    "jobs": "30 per minute",
}


def get_rate_limit(api_type):
    """API 타입별 Rate Limit 정책 조회.
    
    Args:
        api_type: API 타입 (auth, programs_list 등)
        
    Returns:
        str: Rate Limit 정책 (예: "5 per minute")
    """
    return RATE_LIMITS.get(api_type, "30 per minute")
