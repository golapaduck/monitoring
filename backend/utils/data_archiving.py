"""데이터 아카이빙 모듈 (오래된 메트릭 정리)."""

import os
from datetime import datetime, timedelta
from typing import Tuple
from utils.db_pool import get_pool
from utils.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

# 환경 변수에서 설정 로드
METRIC_RETENTION_DAYS = int(os.getenv("METRIC_RETENTION_DAYS", "30"))  # 기본: 30일
EVENT_RETENTION_DAYS = int(os.getenv("EVENT_RETENTION_DAYS", "90"))  # 기본: 90일


def archive_old_metrics(retention_days: int = METRIC_RETENTION_DAYS) -> Tuple[int, int]:
    """오래된 메트릭 데이터 삭제.
    
    Args:
        retention_days: 보관 기간 (일)
    
    Returns:
        Tuple[int, int]: (삭제된 메트릭 수, 절약된 MB)
    """
    pool = get_pool()
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cutoff_timestamp = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # 삭제 전 크기 확인
        before_size = _get_table_size("resource_usage")
        
        # 오래된 메트릭 삭제
        result = pool.execute_update(
            "DELETE FROM resource_usage WHERE timestamp < ?",
            (cutoff_timestamp,)
        )
        
        deleted_count = result.get("rows_affected", 0)
        
        # 삭제 후 크기 확인
        after_size = _get_table_size("resource_usage")
        saved_mb = (before_size - after_size) / (1024 * 1024)
        
        # VACUUM으로 디스크 공간 회수
        pool.execute("VACUUM")
        
        logger.info(
            "메트릭 아카이빙 완료",
            retention_days=retention_days,
            deleted_count=deleted_count,
            saved_mb=round(saved_mb, 2)
        )
        
        return deleted_count, round(saved_mb, 2)
        
    except Exception as e:
        logger.exception("메트릭 아카이빙 실패", error=str(e))
        return 0, 0


def archive_old_events(retention_days: int = EVENT_RETENTION_DAYS) -> Tuple[int, int]:
    """오래된 이벤트 로그 삭제.
    
    Args:
        retention_days: 보관 기간 (일)
    
    Returns:
        Tuple[int, int]: (삭제된 이벤트 수, 절약된 MB)
    """
    pool = get_pool()
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cutoff_timestamp = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # 삭제 전 크기 확인
        before_size = _get_table_size("program_events")
        
        # 오래된 이벤트 삭제
        result = pool.execute_update(
            "DELETE FROM program_events WHERE timestamp < ?",
            (cutoff_timestamp,)
        )
        
        deleted_count = result.get("rows_affected", 0)
        
        # 삭제 후 크기 확인
        after_size = _get_table_size("program_events")
        saved_mb = (before_size - after_size) / (1024 * 1024)
        
        # VACUUM으로 디스크 공간 회수
        pool.execute("VACUUM")
        
        logger.info(
            "이벤트 아카이빙 완료",
            retention_days=retention_days,
            deleted_count=deleted_count,
            saved_mb=round(saved_mb, 2)
        )
        
        return deleted_count, round(saved_mb, 2)
        
    except Exception as e:
        logger.exception("이벤트 아카이빙 실패", error=str(e))
        return 0, 0


def archive_all(
    metric_retention_days: int = METRIC_RETENTION_DAYS,
    event_retention_days: int = EVENT_RETENTION_DAYS
) -> dict:
    """모든 데이터 아카이빙 실행.
    
    Args:
        metric_retention_days: 메트릭 보관 기간 (일)
        event_retention_days: 이벤트 보관 기간 (일)
    
    Returns:
        dict: 아카이빙 결과
    """
    logger.info("데이터 아카이빙 시작")
    
    # 메트릭 아카이빙
    metric_deleted, metric_saved = archive_old_metrics(metric_retention_days)
    
    # 이벤트 아카이빙
    event_deleted, event_saved = archive_old_events(event_retention_days)
    
    total_saved = metric_saved + event_saved
    
    result = {
        "metrics": {
            "deleted": metric_deleted,
            "saved_mb": metric_saved
        },
        "events": {
            "deleted": event_deleted,
            "saved_mb": event_saved
        },
        "total_saved_mb": round(total_saved, 2)
    }
    
    logger.info(
        "데이터 아카이빙 완료",
        total_deleted=metric_deleted + event_deleted,
        total_saved_mb=round(total_saved, 2)
    )
    
    return result


def get_data_statistics() -> dict:
    """데이터베이스 통계 조회.
    
    Returns:
        dict: 데이터베이스 통계
    """
    pool = get_pool()
    
    try:
        # 메트릭 통계
        metric_count = pool.execute(
            "SELECT COUNT(*) as count FROM resource_usage"
        )[0]["count"]
        
        metric_oldest = pool.execute(
            "SELECT MIN(timestamp) as oldest FROM resource_usage"
        )[0]["oldest"]
        
        metric_size = _get_table_size("resource_usage")
        
        # 이벤트 통계
        event_count = pool.execute(
            "SELECT COUNT(*) as count FROM program_events"
        )[0]["count"]
        
        event_oldest = pool.execute(
            "SELECT MIN(timestamp) as oldest FROM program_events"
        )[0]["oldest"]
        
        event_size = _get_table_size("program_events")
        
        # 전체 DB 크기
        db_size = _get_database_size()
        
        return {
            "metrics": {
                "count": metric_count,
                "oldest": metric_oldest,
                "size_mb": round(metric_size / (1024 * 1024), 2)
            },
            "events": {
                "count": event_count,
                "oldest": event_oldest,
                "size_mb": round(event_size / (1024 * 1024), 2)
            },
            "database": {
                "size_mb": round(db_size / (1024 * 1024), 2)
            }
        }
        
    except Exception as e:
        logger.exception("데이터 통계 조회 실패", error=str(e))
        return {}


def _get_table_size(table_name: str) -> int:
    """테이블 크기 조회 (바이트).
    
    Args:
        table_name: 테이블 이름
    
    Returns:
        int: 테이블 크기 (바이트)
    """
    pool = get_pool()
    
    try:
        result = pool.execute(
            f"SELECT SUM(pgsize) as size FROM dbstat WHERE name = ?",
            (table_name,)
        )
        
        if result and result[0]["size"]:
            return result[0]["size"]
        return 0
        
    except Exception:
        # dbstat이 없는 경우 대략적인 크기 추정
        result = pool.execute(
            f"SELECT COUNT(*) * 1000 as size FROM {table_name}"
        )
        return result[0]["size"] if result else 0


def _get_database_size() -> int:
    """데이터베이스 전체 크기 조회 (바이트).
    
    Returns:
        int: 데이터베이스 크기 (바이트)
    """
    from config import DATA_DIR
    from pathlib import Path
    
    db_path = Path(DATA_DIR) / "monitoring.db"
    
    if db_path.exists():
        return db_path.stat().st_size
    return 0
