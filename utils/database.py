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
    
    print("✅ [Database] 데이터베이스 초기화 완료")


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
        print("ℹ️ [Database] 이미 마이그레이션된 데이터가 존재합니다.")
        conn.close()
        return
    
    print("🔄 [Database] JSON에서 SQLite로 마이그레이션 시작...")
    
    # 사용자 마이그레이션
    users_data = load_json(USERS_JSON, {"users": []})
    for user in users_data.get("users", []):
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (user["username"], user["password"], user["role"]))
    
    print(f"✅ [Database] 사용자 {len(users_data.get('users', []))}명 마이그레이션 완료")
    
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
    
    print(f"✅ [Database] 프로그램 {len(programs_data.get('programs', []))}개 마이그레이션 완료")
    
    conn.commit()
    conn.close()
    
    print("✅ [Database] 마이그레이션 완료!")


if __name__ == "__main__":
    # 테스트용
    init_database()
    migrate_from_json()
