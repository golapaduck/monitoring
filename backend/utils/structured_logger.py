"""구조화된 로깅 시스템 (structlog 기반)."""

import structlog
import logging
import sys
from pathlib import Path
from datetime import datetime
from config import DATA_DIR

# 로그 디렉토리 생성
LOG_DIR = Path(DATA_DIR) / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_structured_logging(log_level="INFO", enable_console=True, enable_file=True):
    """구조화된 로깅 설정.
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: 콘솔 출력 활성화
        enable_file: 파일 출력 활성화
    """
    # 로그 레벨 설정
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 기본 로거 설정
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    
    # structlog 프로세서 체인
    processors = [
        # 컨텍스트 변수 추가
        structlog.contextvars.merge_contextvars,
        # 타임스탬프 추가
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        # 스택 정보 추가 (에러 시)
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # 개발 환경: 컬러 출력
    if enable_console:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )
    
    # 프로덕션 환경: JSON 출력
    if enable_file:
        processors.append(
            structlog.processors.JSONRenderer()
        )
    
    # structlog 설정
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """구조화된 로거 인스턴스 반환.
    
    Args:
        name: 로거 이름 (모듈명 권장)
    
    Returns:
        structlog.BoundLogger: 구조화된 로거
    
    사용 예:
        logger = get_logger(__name__)
        logger.info("프로그램 시작", program_id=1, pid=1234)
        logger.error("프로그램 크래시", program_id=1, error="Connection refused")
    """
    return structlog.get_logger(name)


# 로그 레벨별 헬퍼 함수
class StructuredLogger:
    """구조화된 로깅을 위한 헬퍼 클래스."""
    
    def __init__(self, name: str = None):
        """로거 초기화.
        
        Args:
            name: 로거 이름
        """
        self.logger = get_logger(name)
    
    def debug(self, event: str, **kwargs):
        """디버그 로그.
        
        Args:
            event: 이벤트 설명
            **kwargs: 추가 컨텍스트
        """
        self.logger.debug(event, **kwargs)
    
    def info(self, event: str, **kwargs):
        """정보 로그.
        
        Args:
            event: 이벤트 설명
            **kwargs: 추가 컨텍스트
        """
        self.logger.info(event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """경고 로그.
        
        Args:
            event: 이벤트 설명
            **kwargs: 추가 컨텍스트
        """
        self.logger.warning(event, **kwargs)
    
    def error(self, event: str, **kwargs):
        """에러 로그.
        
        Args:
            event: 이벤트 설명
            **kwargs: 추가 컨텍스트
        """
        self.logger.error(event, **kwargs)
    
    def critical(self, event: str, **kwargs):
        """치명적 에러 로그.
        
        Args:
            event: 이벤트 설명
            **kwargs: 추가 컨텍스트
        """
        self.logger.critical(event, **kwargs)
    
    def exception(self, event: str, **kwargs):
        """예외 로그 (스택 트레이스 포함).
        
        Args:
            event: 이벤트 설명
            **kwargs: 추가 컨텍스트
        """
        self.logger.exception(event, **kwargs)


# 전역 로거 인스턴스
_global_logger = None


def init_logging(log_level="INFO"):
    """로깅 시스템 초기화.
    
    Args:
        log_level: 로그 레벨
    """
    global _global_logger
    setup_structured_logging(log_level=log_level)
    _global_logger = StructuredLogger("monitoring")
    return _global_logger


def get_global_logger():
    """전역 로거 반환.
    
    Returns:
        StructuredLogger: 전역 로거 인스턴스
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = init_logging()
    return _global_logger


# 편의 함수
def log_info(event: str, **kwargs):
    """정보 로그 (전역 로거 사용)."""
    get_global_logger().info(event, **kwargs)


def log_warning(event: str, **kwargs):
    """경고 로그 (전역 로거 사용)."""
    get_global_logger().warning(event, **kwargs)


def log_error(event: str, **kwargs):
    """에러 로그 (전역 로거 사용)."""
    get_global_logger().error(event, **kwargs)


def log_debug(event: str, **kwargs):
    """디버그 로그 (전역 로거 사용)."""
    get_global_logger().debug(event, **kwargs)


def log_exception(event: str, **kwargs):
    """예외 로그 (전역 로거 사용)."""
    get_global_logger().exception(event, **kwargs)
