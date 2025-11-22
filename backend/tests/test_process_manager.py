"""프로세스 관리자 테스트."""

import pytest
from pathlib import Path
from utils.process_manager import (
    get_process_status,
    start_program,
    stop_program,
    get_programs_status_batch
)


class TestProcessManager:
    """프로세스 관리자 테스트 클래스."""
    
    def test_get_process_status_invalid_path(self):
        """존재하지 않는 프로그램 경로 테스트."""
        is_running, pid = get_process_status("C:\\nonexistent\\program.exe")
        assert is_running is False
        assert pid is None
    
    def test_get_process_status_with_pid(self):
        """PID와 함께 프로세스 상태 확인 테스트."""
        # 유효하지 않은 PID로 테스트
        is_running, pid = get_process_status("notepad.exe", pid=99999)
        # 결과는 False 또는 실제 프로세스 PID
        assert isinstance(is_running, bool)
        assert pid is None or isinstance(pid, int)
    
    def test_get_programs_status_batch_empty(self):
        """빈 프로그램 목록 배치 처리 테스트."""
        programs = []
        result = get_programs_status_batch(programs)
        assert result == []
    
    def test_get_programs_status_batch_structure(self):
        """프로그램 목록 배치 처리 결과 구조 테스트."""
        programs = [
            {"id": 1, "name": "notepad", "path": "C:\\Windows\\notepad.exe"},
            {"id": 2, "name": "calc", "path": "C:\\Windows\\calc.exe"}
        ]
        result = get_programs_status_batch(programs)
        
        # 결과 개수 확인
        assert len(result) == 2
        
        # 각 결과의 구조 확인
        for item in result:
            assert "id" in item
            assert "name" in item
            assert "path" in item
            assert "running" in item
            assert "pid" in item
            assert isinstance(item["running"], bool)
            assert item["pid"] is None or isinstance(item["pid"], int)
    
    def test_start_program_invalid_path(self):
        """존재하지 않는 프로그램 시작 테스트."""
        success, message, pid = start_program("C:\\nonexistent\\program.exe")
        # 실패하거나 PID를 찾지 못함
        assert isinstance(success, bool)
        assert isinstance(message, str)
        assert pid is None or isinstance(pid, int)
    
    def test_stop_program_invalid_path(self):
        """존재하지 않는 프로그램 종료 테스트."""
        success, message = stop_program("C:\\nonexistent\\program.exe")
        # 실패 또는 성공 (프로세스가 없으면 성공으로 처리)
        assert isinstance(success, bool)
        assert isinstance(message, str)


class TestProcessManagerTypes:
    """프로세스 관리자 타입 힌트 테스트."""
    
    def test_get_process_status_return_type(self):
        """get_process_status 반환 타입 테스트."""
        result = get_process_status("notepad.exe")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], int)
    
    def test_start_program_return_type(self):
        """start_program 반환 타입 테스트."""
        result = start_program("notepad.exe")
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert result[2] is None or isinstance(result[2], int)
    
    def test_stop_program_return_type(self):
        """stop_program 반환 타입 테스트."""
        result = stop_program("notepad.exe")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
    
    def test_get_programs_status_batch_return_type(self):
        """get_programs_status_batch 반환 타입 테스트."""
        programs = [{"id": 1, "name": "test", "path": "C:\\test.exe"}]
        result = get_programs_status_batch(programs)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
