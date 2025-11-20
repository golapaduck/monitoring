"""프로세스 크래시 감지 및 모니터링."""

import threading
import time
from pathlib import Path
from utils.process_manager import get_process_status
from utils.logger import log_program_event
from utils.webhook import send_webhook_notification
from utils.data_manager import load_json
from config import PROGRAMS_JSON


class ProcessMonitor:
    """프로세스 상태를 모니터링하고 예기치 않은 종료를 감지하는 클래스."""
    
    def __init__(self, check_interval=10):
        """
        Args:
            check_interval: 상태 확인 간격 (초)
        """
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.last_status = {}  # {program_name: running_status}
        
    def start(self):
        """모니터링 시작."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True, name="ProcessMonitor")
        self.thread.start()
        print(f"🔍 [Process Monitor] 프로세스 모니터링 시작 (간격: {self.check_interval}초)")
    
    def stop(self):
        """모니터링 중지."""
        if not self.running:
            return
            
        self.running = False
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=2)
            except Exception:
                pass  # 종료 시 발생하는 예외 무시
        print("🛑 [Process Monitor] 프로세스 모니터링 중지")
    
    def _monitor_loop(self):
        """모니터링 루프 (백그라운드 스레드)."""
        while self.running:
            try:
                self._check_processes()
            except Exception as e:
                print(f"⚠️ [Process Monitor] 모니터링 오류: {str(e)}")
            
            # 다음 체크까지 대기
            time.sleep(self.check_interval)
    
    def _check_processes(self):
        """등록된 모든 프로세스 상태 확인."""
        programs_data = load_json(PROGRAMS_JSON, {"programs": []})
        
        for program in programs_data["programs"]:
            program_name = program["name"]
            program_path = program["path"]
            webhook_url = program.get("webhook_url")
            
            # 현재 실행 상태 확인
            is_running = get_process_status(program_path)
            
            # 이전 상태와 비교
            was_running = self.last_status.get(program_name)
            
            # 상태 변화 감지
            if was_running is not None:  # 첫 체크가 아닌 경우
                if was_running and not is_running:
                    # 프로세스가 예기치 않게 종료됨
                    self._handle_unexpected_termination(program_name, webhook_url)
            
            # 현재 상태 저장
            self.last_status[program_name] = is_running
    
    def _handle_unexpected_termination(self, program_name, webhook_url):
        """예기치 않은 프로세스 종료 처리.
        
        Args:
            program_name: 프로그램 이름
            webhook_url: 웹훅 URL
        """
        print(f"💥 [Process Monitor] 예기치 않은 종료 감지: {program_name}")
        
        # 로그 기록
        log_program_event(program_name, "crash", "프로세스가 예기치 않게 종료됨")
        
        # 웹훅 알림 (비동기)
        if webhook_url:
            send_webhook_notification(
                program_name, 
                "crash", 
                "프로세스가 예기치 않게 종료되었습니다. 원인을 확인하세요.", 
                "error",
                webhook_url
            )
        else:
            print(f"ℹ️ [Process Monitor] 웹훅 URL이 설정되지 않아 알림을 전송하지 않습니다: {program_name}")


# 전역 모니터 인스턴스
_monitor = None


def start_process_monitor(check_interval=10):
    """프로세스 모니터 시작.
    
    Args:
        check_interval: 상태 확인 간격 (초)
    """
    global _monitor
    if _monitor is None:
        _monitor = ProcessMonitor(check_interval)
    _monitor.start()


def stop_process_monitor():
    """프로세스 모니터 중지."""
    global _monitor
    if _monitor:
        _monitor.stop()
