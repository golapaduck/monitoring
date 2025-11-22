"""캐싱 유틸리티 테스트."""

import pytest
import time
from utils.cache import Cache, get_cache


class TestCache:
    """캐시 클래스 테스트."""
    
    def test_cache_set_get(self):
        """캐시 저장 및 조회 테스트."""
        cache = Cache(ttl_seconds=300)
        cache.set("key1", "value1")
        
        result = cache.get("key1")
        assert result == "value1"
    
    def test_cache_get_nonexistent(self):
        """존재하지 않는 키 조회 테스트."""
        cache = Cache(ttl_seconds=300)
        result = cache.get("nonexistent")
        assert result is None
    
    def test_cache_delete(self):
        """캐시 삭제 테스트."""
        cache = Cache(ttl_seconds=300)
        cache.set("key1", "value1")
        cache.delete("key1")
        
        result = cache.get("key1")
        assert result is None
    
    def test_cache_clear(self):
        """캐시 전체 삭제 테스트."""
        cache = Cache(ttl_seconds=300)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_ttl_expiration(self):
        """캐시 TTL 만료 테스트."""
        cache = Cache(ttl_seconds=1)  # 1초 TTL
        cache.set("key1", "value1")
        
        # 즉시 조회 - 캐시 히트
        assert cache.get("key1") == "value1"
        
        # 1.1초 대기 - TTL 만료
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_cache_multiple_keys(self):
        """여러 키 캐싱 테스트."""
        cache = Cache(ttl_seconds=300)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
    
    def test_cache_different_types(self):
        """다양한 데이터 타입 캐싱 테스트."""
        cache = Cache(ttl_seconds=300)
        
        # 문자열
        cache.set("str", "value")
        assert cache.get("str") == "value"
        
        # 숫자
        cache.set("int", 42)
        assert cache.get("int") == 42
        
        # 리스트
        cache.set("list", [1, 2, 3])
        assert cache.get("list") == [1, 2, 3]
        
        # 딕셔너리
        cache.set("dict", {"key": "value"})
        assert cache.get("dict") == {"key": "value"}


class TestGlobalCache:
    """글로벌 캐시 인스턴스 테스트."""
    
    def test_get_cache_singleton(self):
        """글로벌 캐시 싱글톤 테스트."""
        cache1 = get_cache()
        cache2 = get_cache()
        
        # 같은 인스턴스여야 함
        assert cache1 is cache2
    
    def test_global_cache_operations(self):
        """글로벌 캐시 동작 테스트."""
        cache = get_cache()
        
        # 기존 데이터 정리
        cache.clear()
        
        # 저장 및 조회
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # 정리
        cache.delete("test_key")


class TestCacheDecorator:
    """캐시 데코레이터 테스트."""
    
    def test_cached_decorator(self):
        """@cached 데코레이터 테스트."""
        cache = Cache(ttl_seconds=300)
        call_count = 0
        
        @cache.cached(ttl_seconds=300)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 첫 호출 - 함수 실행
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # 두 번째 호출 - 캐시 사용
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # 함수가 다시 호출되지 않음
        
        # 다른 인자로 호출 - 함수 실행
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2
