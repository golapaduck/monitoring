"""성능 모니터링 유틸리티.

API 응답 시간, 데이터베이스 쿼리 시간 등을 모니터링합니다.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """성능 모니터링 클래스."""
    
    def __init__(self):
        """성능 모니터 초기화."""
        self.metrics = defaultdict(list)  # {endpoint: [response_times]}
        self.max_history = 100  # 최근 100개 기록만 유지
    
    def record(self, endpoint: str, response_time: float):
        """응답 시간 기록.
        
        Args:
            endpoint: 엔드포인트 이름
            response_time: 응답 시간 (초)
        """
        self.metrics[endpoint].append({
            'timestamp': datetime.now(),
            'response_time': response_time
        })
        
        # 최근 N개만 유지
        if len(self.metrics[endpoint]) > self.max_history:
            self.metrics[endpoint] = self.metrics[endpoint][-self.max_history:]
    
    def get_stats(self, endpoint: str) -> dict:
        """엔드포인트별 통계 조회.
        
        Args:
            endpoint: 엔드포인트 이름
            
        Returns:
            dict: 통계 정보
                - avg: 평균 응답 시간
                - min: 최소 응답 시간
                - max: 최대 응답 시간
                - count: 기록 개수
        """
        if endpoint not in self.metrics or not self.metrics[endpoint]:
            return {
                'avg': 0,
                'min': 0,
                'max': 0,
                'count': 0
            }
        
        times = [m['response_time'] for m in self.metrics[endpoint]]
        
        return {
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'count': len(times)
        }
    
    def get_all_stats(self) -> dict:
        """모든 엔드포인트의 통계 조회.
        
        Returns:
            dict: 모든 엔드포인트의 통계
        """
        return {
            endpoint: self.get_stats(endpoint)
            for endpoint in self.metrics.keys()
        }
    
    def clear(self):
        """모든 메트릭 초기화."""
        self.metrics.clear()


# 글로벌 성능 모니터 인스턴스
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """글로벌 성능 모니터 반환.
    
    Returns:
        PerformanceMonitor: 성능 모니터 인스턴스
    """
    return _performance_monitor


def monitor_performance(endpoint_name: str = None):
    """성능 모니터링 데코레이터.
    
    API 엔드포인트의 응답 시간을 자동으로 기록합니다.
    
    Args:
        endpoint_name: 엔드포인트 이름 (기본: 함수명)
        
    Example:
        @monitor_performance("programs_list")
        def get_programs():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 엔드포인트 이름 결정
            name = endpoint_name or func.__name__
            
            # 시작 시간 기록
            start_time = time.time()
            
            try:
                # 함수 실행
                result = func(*args, **kwargs)
                return result
            finally:
                # 응답 시간 계산 및 기록
                response_time = time.time() - start_time
                _performance_monitor.record(name, response_time)
                
                # 느린 요청 로깅 (1초 이상)
                if response_time > 1.0:
                    logger.warning(
                        f"⚠️ [Performance] 느린 요청 감지: {name} ({response_time:.2f}초)"
                    )
        
        return wrapper
    
    return decorator


def log_slow_queries(threshold: float = 0.1):
    """느린 쿼리 로깅 데코레이터.
    
    Args:
        threshold: 느린 쿼리 판정 시간 (초, 기본: 0.1초)
        
    Example:
        @log_slow_queries(threshold=0.5)
        def database_query():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                
                if elapsed > threshold:
                    logger.warning(
                        f"⚠️ [Database] 느린 쿼리: {func.__name__} ({elapsed:.3f}초)"
                    )
        
        return wrapper
    
    return decorator


# 성능 모니터링 API 엔드포인트
def create_performance_api(app):
    """성능 모니터링 API 엔드포인트 생성.
    
    Args:
        app: Flask 애플리케이션 인스턴스
    """
    from flask import jsonify
    from utils.decorators import require_auth, require_admin
    
    @app.route('/api/admin/performance', methods=['GET'])
    @require_auth
    @require_admin
    def get_performance_stats():
        """성능 통계 조회 (관리자만).
        
        Returns:
            JSON: 모든 엔드포인트의 성능 통계
        """
        stats = _performance_monitor.get_all_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'endpoints': stats,
                'timestamp': datetime.now().isoformat()
            }
        }), 200
    
    @app.route('/api/admin/performance/<endpoint>', methods=['GET'])
    @require_auth
    @require_admin
    def get_endpoint_performance(endpoint):
        """특정 엔드포인트의 성능 통계 조회 (관리자만).
        
        Args:
            endpoint: 엔드포인트 이름
            
        Returns:
            JSON: 엔드포인트의 성능 통계
        """
        stats = _performance_monitor.get_stats(endpoint)
        
        return jsonify({
            'success': True,
            'data': {
                'endpoint': endpoint,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
        }), 200
    
    @app.route('/api/admin/performance', methods=['DELETE'])
    @require_auth
    @require_admin
    def clear_performance_stats():
        """성능 통계 초기화 (관리자만).
        
        Returns:
            JSON: 초기화 결과
        """
        _performance_monitor.clear()
        
        return jsonify({
            'success': True,
            'message': '성능 통계가 초기화되었습니다'
        }), 200
