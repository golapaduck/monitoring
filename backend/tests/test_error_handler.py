"""에러 처리 시스템 테스트."""

import pytest
import psutil
import sqlite3
import requests
from unittest.mock import Mock, patch
from utils.error_handler import (
    handle_process_errors,
    handle_database_errors,
    handle_network_errors,
    retry_on_failure,
    safe_execute,
    ErrorContext,
    RetryConfig,
    log_and_ignore
)


class TestProcessErrorHandling:
    """프로세스 에러 처리 테스트."""
    
    def test_no_such_process_error(self):
        """NoSuchProcess 에러 처리 테스트."""
        @handle_process_errors
        def get_process_info(pid):
            raise psutil.NoSuchProcess(pid)
        
        result = get_process_info(9999)
        assert result is None
    
    def test_access_denied_error(self):
        """AccessDenied 에러 처리 테스트."""
        @handle_process_errors
        def get_process_info(pid):
            raise psutil.AccessDenied(pid)
        
        result = get_process_info(1234)
        assert result is None
    
    def test_zombie_process_error(self):
        """ZombieProcess 에러 처리 테스트."""
        @handle_process_errors
        def get_process_info(pid):
            raise psutil.ZombieProcess(pid)
        
        result = get_process_info(5678)
        assert result is None
    
    def test_successful_execution(self):
        """정상 실행 테스트."""
        @handle_process_errors
        def get_process_info(pid):
            return {"pid": pid, "name": "test.exe"}
        
        result = get_process_info(1234)
        assert result == {"pid": 1234, "name": "test.exe"}


class TestDatabaseErrorHandling:
    """데이터베이스 에러 처리 테스트."""
    
    def test_integrity_error(self):
        """IntegrityError 처리 테스트."""
        @handle_database_errors
        def insert_duplicate():
            raise sqlite3.IntegrityError("UNIQUE constraint failed")
        
        with pytest.raises(sqlite3.IntegrityError):
            insert_duplicate()
    
    def test_operational_error(self):
        """OperationalError 처리 테스트."""
        @handle_database_errors
        def query_locked_table():
            raise sqlite3.OperationalError("database is locked")
        
        with pytest.raises(sqlite3.OperationalError):
            query_locked_table()
    
    def test_successful_query(self):
        """정상 쿼리 테스트."""
        @handle_database_errors
        def query_data():
            return [{"id": 1, "name": "test"}]
        
        result = query_data()
        assert result == [{"id": 1, "name": "test"}]


class TestNetworkErrorHandling:
    """네트워크 에러 처리 테스트."""
    
    def test_timeout_error(self):
        """Timeout 에러 처리 테스트."""
        @handle_network_errors
        def make_request():
            raise requests.exceptions.Timeout("Connection timeout")
        
        result = make_request()
        assert result is None
    
    def test_connection_error(self):
        """ConnectionError 처리 테스트."""
        @handle_network_errors
        def make_request():
            raise requests.exceptions.ConnectionError("Connection refused")
        
        result = make_request()
        assert result is None
    
    def test_http_error(self):
        """HTTPError 처리 테스트."""
        @handle_network_errors
        def make_request():
            response = Mock()
            response.status_code = 404
            raise requests.exceptions.HTTPError(response=response)
        
        result = make_request()
        assert result is None
    
    def test_successful_request(self):
        """정상 요청 테스트."""
        @handle_network_errors
        def make_request():
            return {"status": "success"}
        
        result = make_request()
        assert result == {"status": "success"}


class TestRetryMechanism:
    """재시도 메커니즘 테스트."""
    
    def test_retry_success_on_second_attempt(self):
        """두 번째 시도에서 성공 테스트."""
        attempt_count = [0]
        
        @retry_on_failure(RetryConfig(max_retries=3, delay=0.1))
        def flaky_function():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert attempt_count[0] == 2
    
    def test_retry_failure_after_max_retries(self):
        """최대 재시도 후 실패 테스트."""
        @retry_on_failure(RetryConfig(max_retries=2, delay=0.1))
        def always_fails():
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError):
            always_fails()
    
    def test_no_retry_on_success(self):
        """성공 시 재시도 없음 테스트."""
        attempt_count = [0]
        
        @retry_on_failure(RetryConfig(max_retries=3, delay=0.1))
        def successful_function():
            attempt_count[0] += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert attempt_count[0] == 1


class TestSafeExecute:
    """안전한 실행 테스트."""
    
    def test_safe_execute_success(self):
        """정상 실행 테스트."""
        def add(a, b):
            return a + b
        
        result = safe_execute(add, 2, 3)
        assert result == 5
    
    def test_safe_execute_with_exception(self):
        """예외 발생 시 기본값 반환 테스트."""
        def divide(a, b):
            return a / b
        
        result = safe_execute(divide, 10, 0, default=0)
        assert result == 0
    
    def test_safe_execute_with_kwargs(self):
        """키워드 인자 테스트."""
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        result = safe_execute(greet, name="World", greeting="Hi")
        assert result == "Hi, World!"


class TestErrorContext:
    """에러 컨텍스트 테스트."""
    
    def test_error_context_success(self):
        """정상 실행 테스트."""
        with ErrorContext("테스트 작업", test_id=1):
            result = 2 + 2
        assert result == 4
    
    def test_error_context_with_exception(self):
        """예외 발생 테스트."""
        with pytest.raises(ValueError):
            with ErrorContext("실패 작업", test_id=2):
                raise ValueError("Test error")


class TestLogAndIgnore:
    """로그 후 무시 테스트."""
    
    def test_log_and_ignore_success(self):
        """정상 실행 테스트."""
        @log_and_ignore
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_log_and_ignore_with_exception(self):
        """예외 무시 테스트."""
        @log_and_ignore
        def failing_function():
            raise ValueError("This should be ignored")
        
        result = failing_function()
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
