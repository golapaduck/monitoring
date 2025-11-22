"""SQLite 데이터베이스 관리 모듈."""

import sqlite3
from pathlib import Path
from datetime import datetime
import json
from config import DATA_DIR

# 데이터베이스 파일 경로
DB_PATH = Path(DATA_DIR) / "monitoring.db"


def get_connection():
    """데이터베이스 연결 반환.
    
    Returns:
        sqlite3.Connection: 데이터베이스 연결 객체
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    return conn


def init_database():
    """데이터베이스 초기화 및 테이블 생성."""
    conn = get_connection()
    cursor = conn.cursor()
    
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
    
    # 인덱스 생성
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_programs_name ON programs(name)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_program_events_program_id ON program_events(program_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_program_events_timestamp ON program_events(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_resource_usage_program_id ON resource_usage(program_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_resource_usage_timestamp ON resource_usage(timestamp)
    """)
    
    conn.commit()
    conn.close()
    
    print("[Database] 데이터베이스 초기화 완료")


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
    """모든 프로그램 조회 (웹훅 URL 포함)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM programs ORDER BY id")
    programs = []
    
    for row in cursor.fetchall():
        program = dict(row)
        program_id = program['id']
        
        # 웹훅 URL 조회
        cursor.execute("SELECT url FROM webhook_urls WHERE program_id = ?", (program_id,))
        webhook_urls = [r['url'] for r in cursor.fetchall()]
        program['webhook_urls'] = webhook_urls
        
        programs.append(program)
    
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
    """리소스 사용량 조회 (시간 범위)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM resource_usage 
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
