"""PowerShell 에이전트 시스템."""

import logging
import subprocess
import json
import threading
import queue
import uuid
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """명령 상태."""
    PENDING = "pending"      # 대기 중
    RUNNING = "running"      # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"        # 실패
    TIMEOUT = "timeout"      # 타임아웃


class PowerShellCommand:
    """PowerShell 명령."""
    
    def __init__(self, script: str, timeout: int = 30):
        """명령 초기화.
        
        Args:
            script: PowerShell 스크립트
            timeout: 타임아웃 (초)
        """
        self.id = str(uuid.uuid4())
        self.script = script
        self.timeout = timeout
        self.status = CommandStatus.PENDING
        self.result = None
        self.error = None
        self.output = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "id": self.id,
            "script": self.script[:100] + "..." if len(self.script) > 100 else self.script,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "output": self.output,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": (self.completed_at - self.started_at).total_seconds() 
                       if self.started_at and self.completed_at else None
        }


class PowerShellAgent:
    """PowerShell 에이전트."""
    
    def __init__(self, max_queue_size: int = 100):
        """에이전트 초기화.
        
        Args:
            max_queue_size: 최대 큐 크기
        """
        self.command_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.commands: Dict[str, PowerShellCommand] = {}
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.ps_process: Optional[subprocess.Popen] = None
    
    def start(self) -> None:
        """에이전트 시작."""
        if self.running:
            logger.warning("PowerShell 에이전트가 이미 실행 중입니다")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            name="PowerShellAgent",
            daemon=True
        )
        self.worker_thread.start()
        logger.info("PowerShell 에이전트 시작")
    
    def stop(self) -> None:
        """에이전트 중지."""
        if not self.running:
            return
        
        self.running = False
        
        # PowerShell 프로세스 종료
        if self.ps_process:
            try:
                self.ps_process.terminate()
                self.ps_process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"PowerShell 프로세스 종료 오류: {str(e)}")
        
        # 워커 스레드 종료 대기
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        
        logger.info("PowerShell 에이전트 중지")
    
    def execute(self, script: str, timeout: int = 30) -> str:
        """명령 실행.
        
        Args:
            script: PowerShell 스크립트
            timeout: 타임아웃 (초)
            
        Returns:
            명령 ID
        """
        command = PowerShellCommand(script, timeout)
        
        with self.lock:
            self.commands[command.id] = command
        
        try:
            self.command_queue.put(command, timeout=5)
            logger.debug(f"명령 제출: {command.id}")
            return command.id
        except queue.Full:
            logger.error("명령 큐가 가득 찼습니다")
            raise RuntimeError("명령 큐가 가득 찼습니다")
    
    def get_command(self, command_id: str) -> Optional[PowerShellCommand]:
        """명령 조회.
        
        Args:
            command_id: 명령 ID
            
        Returns:
            명령 객체 또는 None
        """
        with self.lock:
            return self.commands.get(command_id)
    
    def get_all_commands(self) -> Dict[str, Dict[str, Any]]:
        """모든 명령 조회.
        
        Returns:
            명령 딕셔너리
        """
        with self.lock:
            return {
                cmd_id: cmd.to_dict()
                for cmd_id, cmd in self.commands.items()
            }
    
    def _worker_loop(self) -> None:
        """워커 루프."""
        try:
            while self.running:
                try:
                    # 타임아웃으로 주기적으로 running 체크
                    command = self.command_queue.get(timeout=1)
                    self._execute_command(command)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"워커 오류: {str(e)}")
        except Exception as e:
            logger.error(f"워커 루프 오류: {str(e)}")
    
    def _execute_command(self, command: PowerShellCommand) -> None:
        """명령 실행.
        
        Args:
            command: PowerShellCommand 객체
        """
        try:
            command.status = CommandStatus.RUNNING
            command.started_at = datetime.now()
            
            # PowerShell 스크립트 실행
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command.script],
                capture_output=True,
                text=True,
                timeout=command.timeout
            )
            
            command.output = result.stdout
            command.error = result.stderr if result.stderr else None
            command.result = result.returncode == 0
            command.status = CommandStatus.COMPLETED
            
            logger.info(f"명령 완료: {command.id} (반환코드: {result.returncode})")
        
        except subprocess.TimeoutExpired:
            command.status = CommandStatus.TIMEOUT
            command.error = f"타임아웃 ({command.timeout}초)"
            logger.warning(f"명령 타임아웃: {command.id}")
        
        except Exception as e:
            command.status = CommandStatus.FAILED
            command.error = str(e)
            logger.error(f"명령 실패 ({command.id}): {str(e)}")
        
        finally:
            command.completed_at = datetime.now()


# 글로벌 에이전트 인스턴스
_global_agent: Optional[PowerShellAgent] = None


def init_powershell_agent(max_queue_size: int = 100) -> PowerShellAgent:
    """글로벌 PowerShell 에이전트 초기화.
    
    Args:
        max_queue_size: 최대 큐 크기
        
    Returns:
        PowerShellAgent 인스턴스
    """
    global _global_agent
    if _global_agent is None:
        _global_agent = PowerShellAgent(max_queue_size)
        _global_agent.start()
    return _global_agent


def get_powershell_agent() -> PowerShellAgent:
    """글로벌 PowerShell 에이전트 반환.
    
    Returns:
        PowerShellAgent 인스턴스
    """
    global _global_agent
    if _global_agent is None:
        raise RuntimeError("PowerShell 에이전트가 초기화되지 않았습니다. init_powershell_agent()을 먼저 호출하세요.")
    return _global_agent


def execute_powershell(script: str, timeout: int = 30) -> str:
    """PowerShell 명령 실행.
    
    Args:
        script: PowerShell 스크립트
        timeout: 타임아웃 (초)
        
    Returns:
        명령 ID
    """
    agent = get_powershell_agent()
    return agent.execute(script, timeout)


def close_powershell_agent() -> None:
    """글로벌 PowerShell 에이전트 종료."""
    global _global_agent
    if _global_agent is not None:
        _global_agent.stop()
        _global_agent = None
