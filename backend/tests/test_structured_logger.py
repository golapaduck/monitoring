"""구조화된 로깅 시스템 테스트."""

import pytest
from utils.structured_logger import (
    StructuredLogger,
    get_logger,
    init_logging,
    log_info,
    log_error
)


class TestStructuredLogger:
    """구조화된 로거 테스트."""
    
    def test_logger_creation(self):
        """로거 생성 테스트."""
        logger = StructuredLogger("test")
        assert logger is not None
        assert logger.logger is not None
    
    def test_info_logging(self):
        """정보 로그 테스트."""
        logger = StructuredLogger("test")
        # 예외가 발생하지 않아야 함
        logger.info("테스트 이벤트", key="value", number=123)
    
    def test_error_logging(self):
        """에러 로그 테스트."""
        logger = StructuredLogger("test")
        # 예외가 발생하지 않아야 함
        logger.error("에러 이벤트", error="test error", code=500)
    
    def test_debug_logging(self):
        """디버그 로그 테스트."""
        logger = StructuredLogger("test")
        # 예외가 발생하지 않아야 함
        logger.debug("디버그 이벤트", data={"key": "value"})
    
    def test_warning_logging(self):
        """경고 로그 테스트."""
        logger = StructuredLogger("test")
        # 예외가 발생하지 않아야 함
        logger.warning("경고 이벤트", reason="test warning")
    
    def test_exception_logging(self):
        """예외 로그 테스트."""
        logger = StructuredLogger("test")
        try:
            raise ValueError("테스트 예외")
        except ValueError:
            # 예외가 발생하지 않아야 함
            logger.exception("예외 발생", context="test")
    
    def test_get_logger(self):
        """get_logger 함수 테스트."""
        logger = get_logger("test_module")
        assert logger is not None
    
    def test_init_logging(self):
        """로깅 초기화 테스트."""
        logger = init_logging(log_level="DEBUG")
        assert logger is not None
    
    def test_global_log_functions(self):
        """전역 로그 함수 테스트."""
        # 예외가 발생하지 않아야 함
        log_info("정보 로그", key="value")
        log_error("에러 로그", error="test")


class TestLogContext:
    """로그 컨텍스트 테스트."""
    
    def test_log_with_context(self):
        """컨텍스트와 함께 로그 테스트."""
        logger = StructuredLogger("test")
        logger.info(
            "프로그램 시작",
            program_id=1,
            program_name="test.exe",
            pid=1234
        )
    
    def test_log_with_nested_data(self):
        """중첩된 데이터와 함께 로그 테스트."""
        logger = StructuredLogger("test")
        logger.info(
            "복잡한 이벤트",
            data={
                "nested": {
                    "key": "value",
                    "number": 123
                },
                "list": [1, 2, 3]
            }
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
