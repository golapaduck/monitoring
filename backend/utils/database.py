"""SQLite 데이터베이스 관리 모듈."""

import sqlite3
from pathlib import Path
from datetime import datetime
import json
import logging
from contextlib import contextmanager
from config import DATA_DIR
from utils.db_pool import get_pool, init_pool

logger = logging.getLogger(__name__)

# 데이터베이스 파일 경로
DB_PATH = Path(DATA_DIR) / "monitoring.db"


@contextmanager
def get_db_connection():
    """데이터베이스 연결 context manager (자동 커밋/롤백/종료).
    
    사용 예:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("...")
    
    Yields:
        sqlite3.Connection: 데이터베이스 연결 객체
    """
    conn = None
    try:
        pool = get_pool()
        conn = pool.get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
            logger.error(f"❌ [Database] 트랜잭션 롤백: {str(e)}")
        raise
    finally:
        if conn:
            try:
                pool = get_pool()
                pool.return_connection(conn)
            except Exception as e:
                logger.error(f"❌ [Database] 연결 반환 실패: {str(e)}")


def get_connection():
    """데이터베이스 연결 반환 (연결 풀 사용).
    
    Returns:
        sqlite3.Connection: 데이터베이스 연결 객체
    """
    try:
        pool = get_pool()
        return pool.get_connection()
    except RuntimeError:
        # 풀이 초기화되지 않았으면 직접 연결
        logger.debug("DB 연결 풀 미초기화, 직접 연결 사용")
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def init_database():
    """데이터베이스 초기화 및 테이블 생성."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 게임 서버 환경: SQLite WAL 모드 활성화 (동시성 개선)
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")  # 성능 향상
    cursor.execute("PRAGMA cache_size = 10000")  # 캐시 크기 증가 (10MB)
    cursor.execute("PRAGMA wal_autocheckpoint = 1000")  # WAL 파일 크기 제한
    cursor.execute("PRAGMA temp_store = MEMORY")  # 임시 테이블 메모리 사용
    
    logger.info("✅ [Database] WAL 모드 활성화 (게임 서버 환경 최적화)")
    
    # 사용자 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 프로그램 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            args TEXT DEFAULT '',
            pid INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 웹훅 URL 테이블 (다중 웹훅 지원)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS webhook_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
        )
    """)
    
    # 프로그램 이벤트 로그 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
        )
    """)
    
    # 리소스 사용량 기록 테이블 (차트용)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            cpu_percent REAL DEFAULT 0,
            memory_mb REAL DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
        )
    """)
    
    # 웹훅 설정 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS webhook_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 플러그인 설정 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plugin_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            plugin_id TEXT NOT NULL,
            config TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
            UNIQUE(program_id, plugin_id)
        )
    """)
    
    # 인덱스 생성 (쿼리 성능 최적화)
    # 1. 프로그램 테이블 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_programs_name ON programs(name)
    """)
    
    # 2. 프로그램 이벤트 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_program_events_program_id ON program_events(program_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_program_events_timestamp ON program_events(timestamp)
    """)
    
    # 복합 인덱스 (program_id + timestamp로 자주 조회)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_program_events_program_timestamp 
        ON program_events(program_id, timestamp DESC)
    """)
    
    # 3. 리소스 사용량 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_resource_usage_program_id ON resource_usage(program_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_resource_usage_timestamp ON resource_usage(timestamp)
    """)
    
    # 복합 인덱스 (program_id + timestamp로 자주 조회)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_resource_usage_program_timestamp 
        ON resource_usage(program_id, timestamp DESC)
    """)
    
    # 4. 웹훅 URL 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhook_urls_program_id ON webhook_urls(program_id)
    """)
    
    # 5. 플러그인 설정 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_plugin_configs_program_id ON plugin_configs(program_id)
    """)
    
    # 6. 사용자 인덱스
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
    """)
    
    conn.commit()
    
    # Graceful Shutdown 컬럼 추가 (마이그레이션)
    try:
        cursor.execute("""
            ALTER TABLE programs ADD COLUMN shutdown_start INTEGER DEFAULT NULL
        """)
        cursor.execute("""
            ALTER TABLE programs ADD COLUMN shutdown_end INTEGER DEFAULT NULL
        """)
        conn.commit()
        print("[Database] Graceful Shutdown 컬럼 추가 완료")
    except Exception as e:
        # 이미 컬럼이 존재하는 경우 무시
        if "duplicate column name" not in str(e).lower():
            print(f"[Database] Graceful Shutdown 컬럼 추가 실패: {e}")
    
    conn.close()
    
    print("[Database] 데이터베이스 초기화 완료 (인덱스 포함)")


def migrate_from_json():
    """JSON 파일에서 SQLite로 데이터 마이그레이션."""
    from utils.data_manager import load_json
    from config import USERS_JSON, PROGRAMS_JSON
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 기존 데이터 확인
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    if user_count > 0:
        print("[Database] 이미 마이그레이션된 데이터가 존재합니다.")
        conn.close()
        return
    
    print("[Database] JSON에서 SQLite로 마이그레이션 시작...")
    
    # 사용자 마이그레이션
    users_data = load_json(USERS_JSON, {"users": []})
    for user in users_data.get("users", []):
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (user["username"], user["password"], user["role"]))
    
    print(f"[Database] 사용자 {len(users_data.get('users', []))}명 마이그레이션 완료")
    
    # 프로그램 마이그레이션
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    for program in programs_data.get("programs", []):
        cursor.execute("""
            INSERT INTO programs (name, path, args, pid)
            VALUES (?, ?, ?, ?)
        """, (
            program["name"],
            program["path"],
            program.get("args", ""),
            program.get("pid")
        ))
        
        program_id = cursor.lastrowid
        
        # 웹훅 URL 마이그레이션
        webhook_urls = program.get("webhook_urls", [])
        if not webhook_urls and program.get("webhook_url"):
            webhook_urls = [program["webhook_url"]]
        
        for url in webhook_urls:
            if url:
                cursor.execute("""
                    INSERT INTO webhook_urls (program_id, url)
                    VALUES (?, ?)
                """, (program_id, url))
    
    print(f"[Database] 프로그램 {len(programs_data.get('programs', []))}개 마이그레이션 완료")
    
    conn.commit()
    conn.close()
    
    print("[Database] 마이그레이션 완료!")


# === 사용자 관련 함수 ===

def get_all_users():
    """모든 사용자 조회."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


def get_user_by_username(username):
    """사용자명으로 사용자 조회."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_password(username, password):
    """사용자 비밀번호 업데이트."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET password = ? WHERE username = ?
    """, (password, username))
    conn.commit()
    conn.close()


# === 프로그램 관련 함수 ===

def get_all_programs():
    """모든 프로그램 조회 (웹훅 URL 포함 - 최적화)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1단계: 모든 프로그램 조회
    cursor.execute("SELECT * FROM programs ORDER BY id")
    programs = [dict(row) for row in cursor.fetchall()]
    
    if not programs:
        conn.close()
        return programs
    
    # 2단계: 모든 웹훅 URL을 한 번에 조회 (N+1 쿼리 제거)
    program_ids = [p['id'] for p in programs]
    placeholders = ','.join('?' * len(program_ids))
    cursor.execute(f"SELECT program_id, url FROM webhook_urls WHERE program_id IN ({placeholders})", program_ids)
    
    # 3단계: 웹훅 URL을 프로그램별로 그룹화
    webhooks_by_program = {}
    for row in cursor.fetchall():
        program_id = row['program_id']
        url = row['url']
        if program_id not in webhooks_by_program:
            webhooks_by_program[program_id] = []
        webhooks_by_program[program_id].append(url)
    
    # 4단계: 프로그램에 웹훅 URL 추가
    for program in programs:
        program['webhook_urls'] = webhooks_by_program.get(program['id'], [])
    
    conn.close()
    return programs


def get_program_by_id(program_id):
    """ID로 프로그램 조회."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM programs WHERE id = ?", (program_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    program = dict(row)
    
    # 웹훅 URL 조회
    cursor.execute("SELECT url FROM webhook_urls WHERE program_id = ?", (program_id,))
    webhook_urls = [r['url'] for r in cursor.fetchall()]
    program['webhook_urls'] = webhook_urls
    
    conn.close()
    return program


def add_program(name, path, args="", webhook_urls=None):
    """프로그램 추가."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO programs (name, path, args)
        VALUES (?, ?, ?)
    """, (name, path, args))
    
    program_id = cursor.lastrowid
    
    # 웹훅 URL 추가
    if webhook_urls:
        for url in webhook_urls:
            if url:
                cursor.execute("""
                    INSERT INTO webhook_urls (program_id, url)
                    VALUES (?, ?)
                """, (program_id, url))
    
    conn.commit()
    conn.close()
    return program_id


def update_program(program_id, name, path, args="", webhook_urls=None):
    """프로그램 업데이트."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE programs 
        SET name = ?, path = ?, args = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (name, path, args, program_id))
    
    # 기존 웹훅 URL 삭제
    cursor.execute("DELETE FROM webhook_urls WHERE program_id = ?", (program_id,))
    
    # 새 웹훅 URL 추가
    if webhook_urls:
        for url in webhook_urls:
            if url:
                cursor.execute("""
                    INSERT INTO webhook_urls (program_id, url)
                    VALUES (?, ?)
                """, (program_id, url))
    
    conn.commit()
    conn.close()


def delete_program(program_id):
    """프로그램 삭제."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM programs WHERE id = ?", (program_id,))
    conn.commit()
    conn.close()


def update_program_pid(program_id, pid):
    """프로그램 PID 업데이트."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE programs SET pid = ? WHERE id = ?
    """, (pid, program_id))
    conn.commit()
    conn.close()


def remove_program_pid(program_id):
    """프로그램 PID 제거."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE programs SET pid = NULL WHERE id = ?
    """, (program_id,))
    conn.commit()
    conn.close()


def set_graceful_shutdown(program_id, shutdown_seconds):
    """Graceful Shutdown 상태 설정.
    
    Args:
        program_id: 프로그램 ID
        shutdown_seconds: 종료 대기 시간 (초)
    """
    import time
    shutdown_start = int(time.time())
    shutdown_end = shutdown_start + shutdown_seconds
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE programs 
        SET shutdown_start = ?, shutdown_end = ?
        WHERE id = ?
    """, (shutdown_start, shutdown_end, program_id))
    conn.commit()
    conn.close()
    print(f"⏱️ [Database] Graceful Shutdown 설정: 프로그램 {program_id} (종료 예정: {shutdown_seconds}초 후)")


def clear_graceful_shutdown(program_id):
    """Graceful Shutdown 상태 해제."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE programs 
        SET shutdown_start = NULL, shutdown_end = NULL
        WHERE id = ?
    """, (program_id,))
    conn.commit()
    conn.close()


# === 이벤트 로그 함수 ===

def log_program_event(program_id, event_type, details=""):
    """프로그램 이벤트 로그 기록."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO program_events (program_id, event_type, details)
        VALUES (?, ?, ?)
    """, (program_id, event_type, details))
    conn.commit()
    conn.close()


def get_program_events(program_id, limit=100):
    """프로그램 이벤트 로그 조회."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM program_events 
        WHERE program_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (program_id, limit))
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events


# === 리소스 사용량 함수 ===

def record_resource_usage(program_id, cpu_percent, memory_mb):
    """리소스 사용량 기록."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resource_usage (program_id, cpu_percent, memory_mb)
        VALUES (?, ?, ?)
    """, (program_id, cpu_percent, memory_mb))
    conn.commit()
    conn.close()


def get_resource_usage(program_id, hours=24):
    """리소스 사용량 조회 (시간 범위 - 필드 선택 최적화)."""
    conn = get_connection()
    cursor = conn.cursor()
    # 필요한 필드만 선택 (id, timestamp 제외 - 프론트엔드에서 불필요)
    cursor.execute("""
        SELECT program_id, cpu_percent, memory_mb, timestamp 
        FROM resource_usage 
        WHERE program_id = ? 
        AND timestamp >= datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp ASC
    """, (program_id, hours))
    usage = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return usage


def cleanup_old_resource_usage(days=7):
    """오래된 리소스 사용량 데이터 정리."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM resource_usage 
        WHERE timestamp < datetime('now', '-' || ? || ' days')
    """, (days,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


# === 플러그인 관련 함수 ===

def save_plugin_config(program_id, plugin_id, config, enabled=True):
    """플러그인 설정 저장.
    
    Args:
        program_id: 프로그램 ID
        plugin_id: 플러그인 ID
        config: 플러그인 설정 (dict)
        enabled: 활성화 여부
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plugin_configs (program_id, plugin_id, config, enabled)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(program_id, plugin_id) DO UPDATE SET
            config = excluded.config,
            enabled = excluded.enabled,
            updated_at = CURRENT_TIMESTAMP
    """, (program_id, plugin_id, json.dumps(config), 1 if enabled else 0))
    conn.commit()
    conn.close()


def get_plugin_config(program_id, plugin_id):
    """플러그인 설정 조회.
    
    Args:
        program_id: 프로그램 ID
        plugin_id: 플러그인 ID
        
    Returns:
        dict: 플러그인 설정 또는 None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT config, enabled FROM plugin_configs
        WHERE program_id = ? AND plugin_id = ?
    """, (program_id, plugin_id))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "config": json.loads(row["config"]) if row["config"] else {},
            "enabled": bool(row["enabled"])
        }
    return None


def get_program_plugins(program_id):
    """프로그램의 모든 플러그인 설정 조회.
    
    Args:
        program_id: 프로그램 ID
        
    Returns:
        list: 플러그인 설정 목록
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT plugin_id, config, enabled FROM plugin_configs
        WHERE program_id = ?
    """, (program_id,))
    plugins = []
    for row in cursor.fetchall():
        plugins.append({
            "plugin_id": row["plugin_id"],
            "config": json.loads(row["config"]) if row["config"] else {},
            "enabled": bool(row["enabled"])
        })
    conn.close()
    return plugins


def get_all_plugin_configs():
    """모든 플러그인 설정 조회 (서버 시작 시 자동 로드용).
    
    Returns:
        list: 모든 플러그인 설정 목록
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT program_id, plugin_id, config, enabled FROM plugin_configs
        WHERE enabled = 1
    """)
    plugins = []
    for row in cursor.fetchall():
        plugins.append({
            "program_id": row["program_id"],
            "plugin_id": row["plugin_id"],
            "config": json.loads(row["config"]) if row["config"] else {},
            "enabled": bool(row["enabled"])
        })
    conn.close()
    return plugins


def delete_plugin_config(program_id, plugin_id):
    """플러그인 설정 삭제.
    
    Args:
        program_id: 프로그램 ID
        plugin_id: 플러그인 ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM plugin_configs
        WHERE program_id = ? AND plugin_id = ?
    """, (program_id, plugin_id))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # 테스트용
    init_database()
    migrate_from_json()
