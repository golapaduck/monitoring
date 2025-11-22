"""데이터베이스 모듈 테스트."""

import pytest
import sqlite3
from pathlib import Path
import tempfile
import os
from utils.database import (
    init_database,
    get_db_connection,
    create_user,
    get_user_by_username,
    create_program,
    get_program_by_id,
    get_all_programs,
    update_program,
    delete_program
)


@pytest.fixture
def temp_db():
    """임시 데이터베이스 픽스처."""
    # 임시 데이터베이스 파일 생성
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_monitoring.db"
    
    # 환경 변수 설정
    os.environ['DATA_DIR'] = temp_dir
    
    # 데이터베이스 초기화
    init_database()
    
    yield db_path
    
    # 정리
    if db_path.exists():
        db_path.unlink()
    os.rmdir(temp_dir)


class TestDatabaseConnection:
    """데이터베이스 연결 테스트."""
    
    def test_get_db_connection(self, temp_db):
        """Context Manager 연결 테스트."""
        with get_db_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_connection_auto_commit(self, temp_db):
        """자동 커밋 테스트."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("test_user", "hashed_password", "user")
            )
        
        # 새 연결에서 확인
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE username = ?", ("test_user",))
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "test_user"
    
    def test_connection_auto_rollback(self, temp_db):
        """자동 롤백 테스트."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    ("rollback_user", "password", "user")
                )
                # 의도적으로 예외 발생
                raise ValueError("Test rollback")
        except ValueError:
            pass
        
        # 롤백되었는지 확인
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE username = ?", ("rollback_user",))
            result = cursor.fetchone()
            assert result is None


class TestUserOperations:
    """사용자 관련 테스트."""
    
    def test_create_user(self, temp_db):
        """사용자 생성 테스트."""
        user_id = create_user("test_user", "hashed_password", "user")
        assert user_id is not None
        assert user_id > 0
    
    def test_get_user_by_username(self, temp_db):
        """사용자 조회 테스트."""
        create_user("lookup_user", "password", "admin")
        user = get_user_by_username("lookup_user")
        assert user is not None
        assert user["username"] == "lookup_user"
        assert user["role"] == "admin"
    
    def test_get_nonexistent_user(self, temp_db):
        """존재하지 않는 사용자 조회 테스트."""
        user = get_user_by_username("nonexistent")
        assert user is None


class TestProgramOperations:
    """프로그램 관련 테스트."""
    
    def test_create_program(self, temp_db):
        """프로그램 생성 테스트."""
        program_id = create_program(
            name="Test Program",
            path="C:\\test\\program.exe",
            args="--test"
        )
        assert program_id is not None
        assert program_id > 0
    
    def test_get_program_by_id(self, temp_db):
        """프로그램 조회 테스트."""
        program_id = create_program(
            name="Lookup Program",
            path="C:\\test\\lookup.exe"
        )
        program = get_program_by_id(program_id)
        assert program is not None
        assert program["name"] == "Lookup Program"
        assert program["path"] == "C:\\test\\lookup.exe"
    
    def test_get_all_programs(self, temp_db):
        """전체 프로그램 조회 테스트."""
        create_program("Program 1", "C:\\test\\prog1.exe")
        create_program("Program 2", "C:\\test\\prog2.exe")
        create_program("Program 3", "C:\\test\\prog3.exe")
        
        programs = get_all_programs()
        assert len(programs) >= 3
    
    def test_update_program(self, temp_db):
        """프로그램 수정 테스트."""
        program_id = create_program("Original Name", "C:\\test\\original.exe")
        
        success = update_program(
            program_id=program_id,
            name="Updated Name",
            path="C:\\test\\updated.exe",
            args="--updated"
        )
        assert success is True
        
        program = get_program_by_id(program_id)
        assert program["name"] == "Updated Name"
        assert program["path"] == "C:\\test\\updated.exe"
        assert program["args"] == "--updated"
    
    def test_delete_program(self, temp_db):
        """프로그램 삭제 테스트."""
        program_id = create_program("Delete Me", "C:\\test\\delete.exe")
        
        success = delete_program(program_id)
        assert success is True
        
        program = get_program_by_id(program_id)
        assert program is None


class TestDatabaseIntegrity:
    """데이터베이스 무결성 테스트."""
    
    def test_unique_username_constraint(self, temp_db):
        """사용자명 유니크 제약 테스트."""
        create_user("unique_user", "password1", "user")
        
        with pytest.raises(sqlite3.IntegrityError):
            create_user("unique_user", "password2", "admin")
    
    def test_foreign_key_constraint(self, temp_db):
        """외래키 제약 테스트 (웹훅 URL)."""
        # 존재하지 않는 프로그램에 웹훅 추가 시도
        with get_db_connection() as conn:
            cursor = conn.cursor()
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO webhook_urls (program_id, url) VALUES (?, ?)",
                    (99999, "https://example.com/webhook")
                )


class TestTransactions:
    """트랜잭션 테스트."""
    
    def test_transaction_commit(self, temp_db):
        """트랜잭션 커밋 테스트."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("tx_user1", "password", "user")
            )
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("tx_user2", "password", "user")
            )
        
        # 두 사용자 모두 저장되었는지 확인
        user1 = get_user_by_username("tx_user1")
        user2 = get_user_by_username("tx_user2")
        assert user1 is not None
        assert user2 is not None
    
    def test_transaction_rollback_on_error(self, temp_db):
        """에러 발생 시 트랜잭션 롤백 테스트."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    ("rollback1", "password", "user")
                )
                # 의도적으로 제약 위반
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    ("rollback1", "password", "user")  # 중복 사용자명
                )
        except sqlite3.IntegrityError:
            pass
        
        # 첫 번째 사용자도 롤백되었는지 확인
        user = get_user_by_username("rollback1")
        assert user is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
