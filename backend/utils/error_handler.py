"""강화된 에러 처리 시스템."""

import psutil
import sqlite3
import requests
from functools import wraps
from typing import Callable, Any, Optional, Tuple
from utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)


class RetryConfig:
    """재시도 설정."""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        """재시도 설정 초기화.
        
        Args:
            max_retries: 최대 재시도 횟수
            delay: 초기 지연 시간 (초)
            backoff: 지연 시간 증가 배수
        """
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff


def handle_process_errors(func: Callable) -> Callable:
    """프로세스 관련 에러 처리 데코레이터.
    
    psutil 관련 예외를 타입별로 처리합니다.
    
    Args:
        func: 래핑할 함수
    
    Returns:
        Callable: 래핑된 함수
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except psutil.NoSuchProcess as e:
            logger.warning(
                "프로세스 종료됨",
                function=func.__name__,
                pid=e.pid,
                error=str(e)
            )
            return None
        except psutil.AccessDenied as e:
            logger.error(
                "프로세스 접근 권한 없음",
                function=func.__name__,
                pid=e.pid,
                error=str(e)
            )
            return None
        except psutil.ZombieProcess as e:
            logger.warning(
                "좀비 프로세스 감지",
                function=func.__name__,
                pid=e.pid,
                error=str(e)
            )
            return None
        except psutil.TimeoutExpired as e:
            logger.error(
                "프로세스 타임아웃",
                function=func.__name__,
                timeout=e.seconds,
                error=str(e)
            )
            return None
        except Exception as e:
            logger.exception(
                "예상치 못한 프로세스 에러",
                function=func.__name__,
                error_type=type(e).__name__,
                error=str(e)
            )
            return None
    return wrapper


def handle_database_errors(func: Callable) -> Callable:
    """데이터베이스 관련 에러 처리 데코레이터.
    
    SQLite 관련 예외를 타입별로 처리합니다.
    
    Args:
        func: 래핑할 함수
    
    Returns:
        Callable: 래핑된 함수
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.IntegrityError as e:
            logger.error(
                "데이터베이스 무결성 오류",
                function=func.__name__,
                error=str(e)
            )
            raise
        except sqlite3.OperationalError as e:
            logger.error(
                "데이터베이스 작업 오류",
                function=func.__name__,
                error=str(e)
            )
            raise
        except sqlite3.DatabaseError as e:
            logger.error(
                "데이터베이스 오류",
                function=func.__name__,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.exception(
                "예상치 못한 데이터베이스 에러",
                function=func.__name__,
                error_type=type(e).__name__,
                error=str(e)
            )
            raise
    return wrapper


def handle_network_errors(func: Callable) -> Callable:
    """네트워크 관련 에러 처리 데코레이터.
    
    requests 관련 예외를 타입별로 처리합니다.
    
    Args:
        func: 래핑할 함수
    
    Returns:
        Callable: 래핑된 함수
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout as e:
            logger.warning(
                "네트워크 타임아웃",
                function=func.__name__,
                error=str(e)
            )
            return None
        except requests.exceptions.ConnectionError as e:
            logger.warning(
                "네트워크 연결 실패",
                function=func.__name__,
                error=str(e)
            )
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(
                "HTTP 에러",
                function=func.__name__,
                status_code=e.response.status_code if e.response else None,
                error=str(e)
            )
            return None
        except requests.exceptions.RequestException as e:
            logger.error(
                "네트워크 요청 실패",
                function=func.__name__,
                error=str(e)
            )
            return None
        except Exception as e:
            logger.exception(
                "예상치 못한 네트워크 에러",
                function=func.__name__,
                error_type=type(e).__name__,
                error=str(e)
            )
            return None
    return wrapper


def retry_on_failure(
    retry_config: Optional[RetryConfig] = None,
    exceptions: Tuple = (Exception,)
) -> Callable:
    """실패 시 재시도 데코레이터.
    
    Args:
        retry_config: 재시도 설정
        exceptions: 재시도할 예외 타입들
    
    Returns:
        Callable: 데코레이터 함수
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            delay = retry_config.delay
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < retry_config.max_retries:
                        logger.warning(
                            "함수 실행 실패, 재시도 중",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=retry_config.max_retries,
                            delay=delay,
                            error=str(e)
                        )
                        time.sleep(delay)
                        delay *= retry_config.backoff
                    else:
                        logger.error(
                            "최대 재시도 횟수 초과",
                            function=func.__name__,
                            max_retries=retry_config.max_retries,
                            error=str(e)
                        )
            
            # 모든 재시도 실패
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default: Any = None,
    log_error: bool = True,
    **kwargs
) -> Any:
    """안전한 함수 실행 (예외 처리 포함).
    
    Args:
        func: 실행할 함수
        *args: 함수 인자
        default: 예외 발생 시 반환할 기본값
        log_error: 에러 로깅 여부
        **kwargs: 함수 키워드 인자
    
    Returns:
        Any: 함수 실행 결과 또는 기본값
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.exception(
                "함수 실행 실패",
                function=func.__name__,
                error_type=type(e).__name__,
                error=str(e)
            )
        return default


class ErrorContext:
    """에러 컨텍스트 관리자.
    
    with 문으로 사용하여 블록 내 에러를 처리합니다.
    
    사용 예:
        with ErrorContext("프로그램 시작", program_id=1):
            start_program(program_id)
    """
    
    def __init__(self, operation: str, **context):
        """에러 컨텍스트 초기화.
        
        Args:
            operation: 작업 설명
            **context: 추가 컨텍스트
        """
        self.operation = operation
        self.context = context
        self.logger = StructuredLogger(__name__)
    
    def __enter__(self):
        """컨텍스트 진입."""
        self.logger.debug(
            f"{self.operation} 시작",
            **self.context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 종료."""
        if exc_type is None:
            self.logger.debug(
                f"{self.operation} 완료",
                **self.context
            )
            return True
        
        # 예외 발생
        self.logger.error(
            f"{self.operation} 실패",
            error_type=exc_type.__name__,
            error=str(exc_val),
            **self.context
        )
        
        # 예외를 다시 발생시킴
        return False


# 편의 함수
def log_and_ignore(func: Callable) -> Callable:
    """에러를 로깅하고 무시하는 데코레이터.
    
    Args:
        func: 래핑할 함수
    
    Returns:
        Callable: 래핑된 함수
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(
                "에러 무시됨",
                function=func.__name__,
                error_type=type(e).__name__,
                error=str(e)
            )
            return None
    return wrapper
