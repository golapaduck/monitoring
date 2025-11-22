"""캐싱 유틸리티."""

from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import threading


class Cache:
    """간단한 메모리 캐시 구현."""
    
    def __init__(self, ttl_seconds: int = 300):
        """캐시 초기화.
        
        Args:
            ttl_seconds: Time To Live (초 단위)
        """
        self.ttl = timedelta(seconds=ttl_seconds)
        self.data = {}
        self.timestamps = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회.
        
        Args:
            key: 캐시 키
            
        Returns:
            캐시된 값 또는 None
        """
        with self.lock:
            if key not in self.data:
                return None
            
            # TTL 확인
            if datetime.now() - self.timestamps[key] > self.ttl:
                del self.data[key]
                del self.timestamps[key]
                return None
            
            return self.data[key]
    
    def set(self, key: str, value: Any) -> None:
        """캐시에 값 저장.
        
        Args:
            key: 캐시 키
            value: 저장할 값
        """
        with self.lock:
            self.data[key] = value
            self.timestamps[key] = datetime.now()
    
    def delete(self, key: str) -> None:
        """캐시에서 값 삭제.
        
        Args:
            key: 캐시 키
        """
        with self.lock:
            if key in self.data:
                del self.data[key]
                del self.timestamps[key]
    
    def clear(self) -> None:
        """캐시 전체 삭제."""
        with self.lock:
            self.data.clear()
            self.timestamps.clear()
    
    def cached(self, ttl_seconds: int = 300):
        """데코레이터: 함수 결과를 캐싱.
        
        Args:
            ttl_seconds: Time To Live (초 단위)
            
        Example:
            @cache.cached(ttl_seconds=300)
            def get_data():
                return expensive_operation()
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> Any:
                # 캐시 키 생성 (함수명 + 인자)
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # 캐시 확인
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 함수 실행 및 캐싱
                result = func(*args, **kwargs)
                self.set(cache_key, result)
                return result
            
            return wrapper
        return decorator


# 글로벌 캐시 인스턴스
_global_cache = Cache(ttl_seconds=300)


def get_cache() -> Cache:
    """글로벌 캐시 인스턴스 반환."""
    return _global_cache
