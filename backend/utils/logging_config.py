"""표준 로깅 시스템 설정.

Python logging 모듈을 사용한 표준화된 로깅 시스템.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# 로그 디렉토리
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """표준화된 로거 설정.
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        log_file: 로그 파일 이름 (None이면 파일 로깅 안 함)
        level: 로그 레벨 (기본: INFO)
        max_bytes: 로그 파일 최대 크기
        backup_count: 백업 파일 수
    
    Returns:
        설정된 Logger 인스턴스
    
    Example:
        logger = setup_logger(__name__, 'programs.log')
        logger.info("프로그램 시작")
        logger.error("오류 발생")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 이미 핸들러가 있으면 중복 방지
    if logger.handlers:
        return logger
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러 (항상 추가)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택적)
    if log_file:
        file_path = LOGS_DIR / log_file
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """기존 로거 가져오기 또는 새로 생성.
    
    Args:
        name: 로거 이름
    
    Returns:
        Logger 인스턴스
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


# 미리 정의된 로거들
api_logger = setup_logger('api', 'api.log')
process_logger = setup_logger('process', 'process.log')
plugin_logger = setup_logger('plugin', 'plugin.log')
database_logger = setup_logger('database', 'database.log')
websocket_logger = setup_logger('websocket', 'websocket.log')
