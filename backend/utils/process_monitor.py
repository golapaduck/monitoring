"""프로세스 크래시 감지 및 모니터링."""

import threading
import time
import psutil
from utils.process_manager import get_process_status
from utils.webhook import send_webhook_notification
from utils.database import get_all_programs, log_program_event, record_resource_usage
from utils.websocket import emit_program_status, emit_resource_update


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
        self.recent_stops = set()  # 최근 의도적으로 종료된 프로그램 이름
        
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
        """등록된 모든 프로세스 상태 확인 (배치 처리 최적화)."""
        programs = get_all_programs()
        
        # 1단계: 배치로 모든 프로그램 상태 조회 (한 번의 PowerShell 호출)
        from utils.process_manager import get_programs_status_batch
        programs_with_status = get_programs_status_batch(programs)
        
        # 2단계: 상태 변화 감지 및 메트릭 수집
        for program in programs_with_status:
            program_id = program["id"]
            program_name = program["name"]
            webhook_urls = program.get("webhook_urls")
            is_running = program.get("running", False)
            current_pid = program.get("pid")
            
            # CPU/메모리 사용량 수집 (실행 중인 경우만)
            if is_running and current_pid:
                self._collect_metrics(program_id, current_pid)
            
            # 이전 상태와 비교
            was_running = self.last_status.get(program_name)
            
            # 상태 변화 감지
            if was_running is not None:  # 첫 체크가 아닌 경우
                if was_running and not is_running:
                    # 의도적 종료인지 확인
                    if program_name in self.recent_stops:
                        # 의도적 종료 - 웹훅 전송 안 함
                        print(f"ℹ️ [Process Monitor] 의도적 종료 감지: {program_name}")
                        self.recent_stops.remove(program_name)
                    else:
                        # 프로세스가 예기치 않게 종료됨
                        self._handle_unexpected_termination(program_id, program_name, webhook_urls)
                    
                    # 웹소켓으로 상태 변경 전송
                    emit_program_status(program_id, {
                        'running': False,
                        'pid': None
                    })
                elif not was_running and is_running:
                    # 프로세스가 시작됨
                    emit_program_status(program_id, {
                        'running': True,
                        'pid': current_pid
                    })
            
            # 현재 상태 저장
            self.last_status[program_name] = is_running
    
    def _collect_metrics(self, program_id, pid):
        """프로세스의 CPU/메모리 사용량 수집 (최적화).
        
        Args:
            program_id: 프로그램 ID
            pid: 프로세스 ID
        """
        try:
            # PowerShell 에이전트 사용 (배치 처리 가능)
            try:
                from utils.powershell_agent import get_powershell_agent
                agent = get_powershell_agent()
                
                # PowerShell 스크립트: 프로세스 메트릭 조회
                script = f"""
                $proc = Get-Process -Id {pid} -ErrorAction SilentlyContinue
                if ($proc) {{
                    @{{
                        CPU = [math]::Round($proc.CPU, 2)
                        Memory = [math]::Round($proc.WorkingSet / 1MB, 2)
                    }} | ConvertTo-Json
                }}
                """
                
                command_id = agent.execute(script, timeout=5)
                command = agent.get_command(command_id)
                
                # 명령 완료 대기 (최대 5초)
                import time
                for _ in range(50):
                    if command.completed_at:
                        break
                    time.sleep(0.1)
                
                if command.result and command.output:
                    import json
                    try:
                        metrics = json.loads(command.output)
                        cpu_percent = metrics.get('CPU', 0)
                        memory_mb = metrics.get('Memory', 0)
                        
                        # 데이터베이스에 기록
                        record_resource_usage(program_id, cpu_percent, memory_mb)
                        
                        # 웹소켓으로 리소스 업데이트 전송
                        emit_resource_update(program_id, {
                            'cpu_percent': round(cpu_percent, 2),
                            'memory_mb': round(memory_mb, 2)
                        })
                    except json.JSONDecodeError:
                        # PowerShell 파싱 실패 시 psutil 폴백
                        self._collect_metrics_psutil(program_id, pid)
                else:
                    # PowerShell 실패 시 psutil 폴백
                    self._collect_metrics_psutil(program_id, pid)
            
            except RuntimeError:
                # 에이전트 미초기화 시 psutil 사용
                self._collect_metrics_psutil(program_id, pid)
        
        except Exception as e:
            print(f"⚠️ [Process Monitor] 메트릭 수집 오류 (PID {pid}): {str(e)}")
    
    def _collect_metrics_psutil(self, program_id, pid):
        """psutil을 사용한 메트릭 수집 (폴백).
        
        Args:
            program_id: 프로그램 ID
            pid: 프로세스 ID
        """
        try:
            process = psutil.Process(pid)
            
            # CPU 사용률 (%) - interval=0으로 즉시 반환
            cpu_percent = process.cpu_percent(interval=0)
            
            # 메모리 사용량 (MB)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # bytes to MB
            
            # 데이터베이스에 기록
            record_resource_usage(program_id, cpu_percent, memory_mb)
            
            # 웹소켓으로 리소스 업데이트 전송
            emit_resource_update(program_id, {
                'cpu_percent': round(cpu_percent, 2),
                'memory_mb': round(memory_mb, 2)
            })
        
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # 프로세스가 종료되었거나 접근 권한이 없는 경우 무시
            pass
        except Exception as e:
            print(f"⚠️ [Process Monitor] psutil 메트릭 수집 오류 (PID {pid}): {str(e)}")
    
    def _handle_unexpected_termination(self, program_id, program_name, webhook_urls):
        """예기치 않은 프로세스 종료 처리.
        
        Args:
            program_id: 프로그램 ID
            program_name: 프로그램 이름
            webhook_urls: 웹훅 URL (list)
        """
        print(f"💥 [Process Monitor] 예기치 않은 종료 감지: {program_name}")
        
        # 로그 기록 (SQLite)
        log_program_event(program_id, "crash", "프로세스가 예기치 않게 종료됨")
        
        # 웹훅 알림 (비동기, 다중 URL 지원)
        if webhook_urls:
            send_webhook_notification(
                program_name, 
                "crash", 
                "프로세스가 예기치 않게 종료되었습니다. 원인을 확인하세요.", 
                "error",
                webhook_urls
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
    
    # 이미 실행 중이면 재시작하지 않음
    if not _monitor.running:
        _monitor.start()


def stop_process_monitor():
    """프로세스 모니터 중지."""
    global _monitor
    if _monitor:
        _monitor.stop()


def mark_intentional_stop(program_name):
    """프로그램이 의도적으로 종료되었음을 표시.
    
    Args:
        program_name: 프로그램 이름
    """
    global _monitor
    if _monitor:
        _monitor.recent_stops.add(program_name)
        print(f"✅ [Process Monitor] 의도적 종료 등록: {program_name}")
