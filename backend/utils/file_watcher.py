"""파일 감시 시스템 (Watchdog 기반)."""

import logging
from pathlib import Path
from typing import Callable, Optional, List
import threading
import time

logger = logging.getLogger(__name__)


class FileWatcher:
    """파일 변경 감시자."""
    
    def __init__(self, watch_path: str, callback: Callable[[str], None], 
                 extensions: Optional[List[str]] = None, debounce_seconds: float = 1.0):
        """파일 감시자 초기화.
        
        Args:
            watch_path: 감시할 디렉토리 경로
            callback: 파일 변경 시 호출할 콜백 함수
            extensions: 감시할 파일 확장자 (예: ['.log', '.txt'])
            debounce_seconds: 이벤트 디바운스 시간 (초)
        """
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.extensions = extensions
        self.debounce_seconds = debounce_seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_modified_times = {}
    
    def start(self) -> None:
        """파일 감시 시작."""
        if self.running:
            logger.warning("파일 감시자가 이미 실행 중입니다")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info(f"파일 감시 시작: {self.watch_path}")
    
    def stop(self) -> None:
        """파일 감시 중지."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("파일 감시 중지")
    
    def _watch_loop(self) -> None:
        """파일 감시 루프."""
        try:
            while self.running:
                self._check_files()
                time.sleep(self.debounce_seconds)
        except Exception as e:
            logger.error(f"파일 감시 오류: {str(e)}")
    
    def _check_files(self) -> None:
        """파일 변경 확인."""
        if not self.watch_path.exists():
            return
        
        try:
            for file_path in self.watch_path.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # 확장자 필터링
                if self.extensions and file_path.suffix not in self.extensions:
                    continue
                
                # 수정 시간 확인
                try:
                    mtime = file_path.stat().st_mtime
                    last_mtime = self.last_modified_times.get(str(file_path), 0)
                    
                    if mtime > last_mtime:
                        self.last_modified_times[str(file_path)] = mtime
                        
                        # 콜백 호출
                        try:
                            self.callback(str(file_path))
                        except Exception as e:
                            logger.error(f"콜백 실행 오류: {str(e)}")
                
                except (OSError, FileNotFoundError):
                    # 파일이 삭제되었거나 접근 불가
                    self.last_modified_times.pop(str(file_path), None)
        
        except Exception as e:
            logger.error(f"파일 확인 오류: {str(e)}")


class LogFileWatcher:
    """로그 파일 감시자."""
    
    def __init__(self, log_dir: str):
        """로그 파일 감시자 초기화.
        
        Args:
            log_dir: 로그 디렉토리 경로
        """
        self.log_dir = log_dir
        self.watcher = FileWatcher(
            watch_path=log_dir,
            callback=self._on_log_change,
            extensions=['.log'],
            debounce_seconds=2.0
        )
    
    def _on_log_change(self, file_path: str) -> None:
        """로그 파일 변경 시 호출."""
        logger.debug(f"로그 파일 변경 감지: {file_path}")
        # 필요시 추가 처리
    
    def start(self) -> None:
        """로그 감시 시작."""
        self.watcher.start()
    
    def stop(self) -> None:
        """로그 감시 중지."""
        self.watcher.stop()


class ProgramFileWatcher:
    """프로그램 파일 감시자."""
    
    def __init__(self, watch_path: str, on_change: Callable[[str], None]):
        """프로그램 파일 감시자 초기화.
        
        Args:
            watch_path: 감시할 경로
            on_change: 파일 변경 시 호출할 콜백
        """
        self.watcher = FileWatcher(
            watch_path=watch_path,
            callback=on_change,
            debounce_seconds=1.0
        )
    
    def start(self) -> None:
        """감시 시작."""
        self.watcher.start()
    
    def stop(self) -> None:
        """감시 중지."""
        self.watcher.stop()
