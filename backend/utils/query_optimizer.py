"""데이터베이스 쿼리 최적화 유틸리티.

대용량 데이터 조회 시 메모리 효율적인 스트리밍 처리를 제공합니다.
"""

import logging
from typing import Generator, Any, List, Dict
from utils.database import get_connection
from utils.prometheus_metrics import record_db_query
import time

logger = logging.getLogger(__name__)


def stream_resource_usage(program_id: int, hours: int = 24, batch_size: int = 1000) -> Generator[Dict[str, Any], None, None]:
    """리소스 사용량을 배치로 스트리밍 조회 (메모리 효율적).
    
    대용량 데이터를 한 번에 로드하지 않고 배치 단위로 처리합니다.
    
    Args:
        program_id: 프로그램 ID
        hours: 조회 시간 범위 (기본: 24시간)
        batch_size: 배치 크기 (기본: 1000개)
        
    Yields:
        리소스 사용량 데이터 (배치 단위)
        
    Example:
        for batch in stream_resource_usage(1, hours=24):
            for metric in batch:
                process_metric(metric)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    start_time = time.time()
    
    try:
        # 오프셋 기반 배치 처리
        offset = 0
        while True:
            cursor.execute("""
                SELECT program_id, cpu_percent, memory_mb, timestamp 
                FROM resource_usage 
                WHERE program_id = ? 
                AND timestamp >= datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
            """, (program_id, hours, batch_size, offset))
            
            batch = [dict(row) for row in cursor.fetchall()]
            
            if not batch:
                break
            
            yield batch
            offset += batch_size
        
        # 메트릭 기록
        elapsed = time.time() - start_time
        record_db_query('select_streaming', elapsed)
        
    finally:
        conn.close()


def stream_program_events(program_id: int, limit: int = 10000, batch_size: int = 500) -> Generator[List[Dict[str, Any]], None, None]:
    """프로그램 이벤트를 배치로 스트리밍 조회 (메모리 효율적).
    
    Args:
        program_id: 프로그램 ID
        limit: 최대 조회 개수
        batch_size: 배치 크기
        
    Yields:
        프로그램 이벤트 배치
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    start_time = time.time()
    
    try:
        offset = 0
        total_fetched = 0
        
        while total_fetched < limit:
            remaining = limit - total_fetched
            fetch_size = min(batch_size, remaining)
            
            cursor.execute("""
                SELECT id, program_id, event_type, details, timestamp 
                FROM program_events 
                WHERE program_id = ? 
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (program_id, fetch_size, offset))
            
            batch = [dict(row) for row in cursor.fetchall()]
            
            if not batch:
                break
            
            yield batch
            offset += fetch_size
            total_fetched += len(batch)
        
        # 메트릭 기록
        elapsed = time.time() - start_time
        record_db_query('select_streaming', elapsed)
        
    finally:
        conn.close()


def bulk_insert_resource_usage(metrics: List[Dict[str, Any]], batch_size: int = 100) -> int:
    """리소스 사용량을 배치로 삽입 (메모리 효율적).
    
    Args:
        metrics: 리소스 사용량 데이터 리스트
        batch_size: 배치 크기
        
    Returns:
        삽입된 행 수
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    start_time = time.time()
    total_inserted = 0
    
    try:
        for i in range(0, len(metrics), batch_size):
            batch = metrics[i:i + batch_size]
            
            cursor.executemany("""
                INSERT INTO resource_usage (program_id, cpu_percent, memory_mb)
                VALUES (?, ?, ?)
            """, [(m['program_id'], m['cpu_percent'], m['memory_mb']) for m in batch])
            
            total_inserted += len(batch)
        
        conn.commit()
        
        # 메트릭 기록
        elapsed = time.time() - start_time
        record_db_query('insert_batch', elapsed)
        
        logger.info(f"배치 삽입 완료: {total_inserted}개 행 ({elapsed:.2f}초)")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"배치 삽입 오류: {str(e)}")
        raise
    finally:
        conn.close()
    
    return total_inserted


def cleanup_old_data(days: int = 30, batch_size: int = 1000) -> int:
    """오래된 데이터를 배치로 삭제 (메모리 효율적).
    
    Args:
        days: 보관 기간 (기본: 30일)
        batch_size: 배치 크기
        
    Returns:
        삭제된 행 수
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    start_time = time.time()
    total_deleted = 0
    
    try:
        while True:
            cursor.execute("""
                DELETE FROM resource_usage 
                WHERE id IN (
                    SELECT id FROM resource_usage 
                    WHERE timestamp < datetime('now', '-' || ? || ' days')
                    LIMIT ?
                )
            """, (days, batch_size))
            
            deleted = cursor.rowcount
            if deleted == 0:
                break
            
            total_deleted += deleted
            conn.commit()
            
            logger.debug(f"배치 삭제: {deleted}개 행")
        
        # 메트릭 기록
        elapsed = time.time() - start_time
        record_db_query('delete_batch', elapsed)
        
        logger.info(f"데이터 정리 완료: {total_deleted}개 행 삭제 ({elapsed:.2f}초)")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"데이터 정리 오류: {str(e)}")
        raise
    finally:
        conn.close()
    
    return total_deleted


def optimize_database():
    """데이터베이스 최적화 (VACUUM, ANALYZE).
    
    주기적으로 실행하여 성능을 유지합니다.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    start_time = time.time()
    
    try:
        # VACUUM: 데이터베이스 파일 크기 감소
        logger.info("데이터베이스 VACUUM 시작...")
        cursor.execute("VACUUM")
        
        # ANALYZE: 쿼리 최적화 통계 업데이트
        logger.info("데이터베이스 ANALYZE 시작...")
        cursor.execute("ANALYZE")
        
        conn.commit()
        
        elapsed = time.time() - start_time
        logger.info(f"데이터베이스 최적화 완료 ({elapsed:.2f}초)")
        
    except Exception as e:
        logger.error(f"데이터베이스 최적화 오류: {str(e)}")
        raise
    finally:
        conn.close()


# 메모리 사용 최적화 설정
class MemoryOptimizedQuery:
    """메모리 최적화된 쿼리 실행기."""
    
    @staticmethod
    def execute_with_limit(query: str, params: tuple = (), limit: int = 1000) -> List[Dict[str, Any]]:
        """제한된 결과 수로 쿼리 실행.
        
        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터
            limit: 최대 결과 수
            
        Returns:
            쿼리 결과 (최대 limit개)
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        start_time = time.time()
        
        try:
            # LIMIT 추가
            if 'LIMIT' not in query.upper():
                query = f"{query} LIMIT {limit}"
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # 메트릭 기록
            elapsed = time.time() - start_time
            record_db_query('select_limited', elapsed)
            
            return results
            
        finally:
            conn.close()
    
    @staticmethod
    def execute_scalar(query: str, params: tuple = ()) -> Any:
        """단일 값을 반환하는 쿼리 실행 (메모리 효율적).
        
        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터
            
        Returns:
            쿼리 결과 (단일 값)
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        start_time = time.time()
        
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            # 메트릭 기록
            elapsed = time.time() - start_time
            record_db_query('select_scalar', elapsed)
            
            return result[0] if result else None
            
        finally:
            conn.close()
