"""캐싱 유틸리티 (이벤트 기반 무효화 지원)."""

from typing import Any, Optional, Callable, List, Set
from datetime import datetime, timedelta
import threading
import re
from collections import defaultdict


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
        
        # 캐시 무효화 관련
        self.tags = defaultdict(set)  # tag -> set of keys
        self.key_tags = defaultdict(set)  # key -> set of tags
        
        # 캐시 통계
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'invalidations': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회.
        
        Args:
            key: 캐시 키
            
        Returns:
            캐시된 값 또는 None
        """
        with self.lock:
            if key not in self.data:
                self.stats['misses'] += 1
                return None
            
            # TTL 확인
            if datetime.now() - self.timestamps[key] > self.ttl:
                self._delete_key(key)
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            return self.data[key]
    
    def set(self, key: str, value: Any, tags: Optional[List[str]] = None) -> None:
        """캐시에 값 저장.
        
        Args:
            key: 캐시 키
            value: 저장할 값
            tags: 캐시 태그 목록 (무효화용)
        """
        with self.lock:
            self.data[key] = value
            self.timestamps[key] = datetime.now()
            self.stats['sets'] += 1
            
            # 태그 등록
            if tags:
                for tag in tags:
                    self.tags[tag].add(key)
                    self.key_tags[key].add(tag)
    
    def _delete_key(self, key: str) -> None:
        """내부용: 캐시 키 삭제 (락 없이).
        
        Args:
            key: 캐시 키
        """
        if key in self.data:
            del self.data[key]
            del self.timestamps[key]
            
            # 태그 정리
            if key in self.key_tags:
                for tag in self.key_tags[key]:
                    self.tags[tag].discard(key)
                del self.key_tags[key]
    
    def delete(self, key: str) -> None:
        """캐시에서 값 삭제.
        
        Args:
            key: 캐시 키
        """
        with self.lock:
            self._delete_key(key)
            self.stats['deletes'] += 1
    
    def clear(self) -> None:
        """캐시 전체 삭제."""
        with self.lock:
            self.data.clear()
            self.timestamps.clear()
            self.tags.clear()
            self.key_tags.clear()
    
    def invalidate_by_tag(self, tag: str) -> int:
        """태그로 캐시 무효화.
        
        Args:
            tag: 무효화할 태그
            
        Returns:
            int: 무효화된 캐시 수
        
        Example:
            cache.set("program:1", data, tags=["program", "program:1"])
            cache.invalidate_by_tag("program:1")  # program:1 관련 캐시 모두 삭제
        """
        with self.lock:
            if tag not in self.tags:
                return 0
            
            keys_to_delete = list(self.tags[tag])
            for key in keys_to_delete:
                self._delete_key(key)
            
            del self.tags[tag]
            self.stats['invalidations'] += len(keys_to_delete)
            return len(keys_to_delete)
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """패턴으로 캐시 무효화.
        
        Args:
            pattern: 정규식 패턴
            
        Returns:
            int: 무효화된 캐시 수
        
        Example:
            cache.invalidate_by_pattern(r"^program:.*")  # program:로 시작하는 모든 캐시 삭제
        """
        with self.lock:
            regex = re.compile(pattern)
            keys_to_delete = [key for key in self.data.keys() if regex.match(key)]
            
            for key in keys_to_delete:
                self._delete_key(key)
            
            self.stats['invalidations'] += len(keys_to_delete)
            return len(keys_to_delete)
    
    def invalidate_multiple_tags(self, tags: List[str]) -> int:
        """여러 태그로 캐시 무효화.
        
        Args:
            tags: 무효화할 태그 목록
            
        Returns:
            int: 무효화된 캐시 수
        """
        total_invalidated = 0
        for tag in tags:
            total_invalidated += self.invalidate_by_tag(tag)
        return total_invalidated
    
    def get_stats(self) -> dict:
        """캐시 통계 조회.
        
        Returns:
            dict: 캐시 통계
        """
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self.stats,
                'total_requests': total_requests,
                'hit_rate': round(hit_rate, 2),
                'cache_size': len(self.data),
                'tag_count': len(self.tags)
            }
    
    def reset_stats(self) -> None:
        """캐시 통계 초기화."""
        with self.lock:
            self.stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0,
                'invalidations': 0
            }
    
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
