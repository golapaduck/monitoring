"""데이터베이스 연결 풀 관리."""

import sqlite3
from typing import Optional
from pathlib import Path
import threading
import logging

logger = logging.getLogger(__name__)


class DatabasePool:
    """SQLite 연결 풀 관리자 (동시성 최적화)."""
    
    def __init__(self, db_path: str, pool_size: int = 20):
        """연결 풀 초기화.
        
        Args:
            db_path: 데이터베이스 파일 경로
            pool_size: 풀 크기 (기본값: 20 - 동시성 개선)
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections = []
        self.available = []
        self.lock = threading.Lock()
        self.stats = {
            'total_acquired': 0,
            'total_released': 0,
            'max_wait_time': 0
        }
        self._init_pool()
    
    def _init_pool(self) -> None:
        """연결 풀 초기화."""
        with self.lock:
            for _ in range(self.pool_size):
                conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=10.0
                )
                conn.row_factory = sqlite3.Row
                self.connections.append(conn)
                self.available.append(conn)
            
            logger.info(f"DB 연결 풀 초기화: {self.pool_size}개 연결")
    
    def get_connection(self) -> sqlite3.Connection:
        """연결 풀에서 연결 획득.
        
        Returns:
            sqlite3.Connection 객체
        """
        with self.lock:
            if not self.available:
                # 풀이 비어있으면 새 연결 생성
                conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=10.0
                )
                conn.row_factory = sqlite3.Row
                logger.debug("새 DB 연결 생성 (풀 부족)")
                return conn
            
            # 사용 가능한 연결 반환
            conn = self.available.pop()
            return conn
    
    def return_connection(self, conn: sqlite3.Connection) -> None:
        """연결을 풀에 반환.
        
        Args:
            conn: 반환할 연결
        """
        with self.lock:
            if len(self.available) < self.pool_size:
                self.available.append(conn)
            else:
                # 풀이 가득 차면 연결 종료
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"연결 종료 오류: {str(e)}")
    
    def close_all(self) -> None:
        """모든 연결 종료."""
        with self.lock:
            for conn in self.connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"연결 종료 오류: {str(e)}")
            
            self.connections.clear()
            self.available.clear()
            logger.info("DB 연결 풀 종료")
    
    def execute(self, query: str, params: tuple = ()) -> list:
        """쿼리 실행 (SELECT).
        
        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터
            
        Returns:
            쿼리 결과 리스트
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            self.return_connection(conn)
    
    def execute_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        """쿼리 실행 (단일 결과).
        
        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터
            
        Returns:
            쿼리 결과 또는 None
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            self.return_connection(conn)
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """쿼리 실행 (INSERT/UPDATE/DELETE).
        
        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터
            
        Returns:
            영향받은 행 수
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"DB 업데이트 오류: {str(e)}")
            raise
        finally:
            self.return_connection(conn)


# 글로벌 연결 풀 인스턴스
_global_pool: Optional[DatabasePool] = None


def init_pool(db_path: str, pool_size: int = 5) -> DatabasePool:
    """글로벌 연결 풀 초기화.
    
    Args:
        db_path: 데이터베이스 파일 경로
        pool_size: 풀 크기
        
    Returns:
        DatabasePool 인스턴스
    """
    global _global_pool
    if _global_pool is None:
        _global_pool = DatabasePool(db_path, pool_size)
    return _global_pool


def get_pool() -> DatabasePool:
    """글로벌 연결 풀 반환.
    
    Returns:
        DatabasePool 인스턴스
    """
    global _global_pool
    if _global_pool is None:
        raise RuntimeError("DB 연결 풀이 초기화되지 않았습니다. init_pool()을 먼저 호출하세요.")
    return _global_pool


def close_pool() -> None:
    """글로벌 연결 풀 종료."""
    global _global_pool
    if _global_pool is not None:
        _global_pool.close_all()
        _global_pool = None
