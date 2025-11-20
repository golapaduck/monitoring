"""프로세스 관리 유틸리티 함수들."""

import subprocess
from pathlib import Path
import psutil


def get_process_status(program_path):
    """프로그램 경로로 프로세스 실행 여부 확인.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        
    Returns:
        bool: 프로세스가 실행 중이면 True, 아니면 False
    """
    try:
        program_name = Path(program_path).name
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['exe'] and Path(proc.info['exe']).name.lower() == program_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception:
        return False


def start_program(program_path, args=""):
    """프로그램 실행.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        args: 실행 인자 (선택사항)
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        cmd = f'"{program_path}"'
        if args:
            cmd += f" {args}"
        
        # PowerShell을 통해 백그라운드로 실행
        subprocess.Popen(
            ["powershell", "-Command", f"Start-Process -FilePath {cmd}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True, "프로그램이 실행되었습니다."
    except Exception as e:
        return False, f"실행 실패: {str(e)}"


def stop_program(program_path):
    """프로그램 종료.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        program_name = Path(program_path).name
        killed = False
        
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['exe'] and Path(proc.info['exe']).name.lower() == program_name.lower():
                    proc.terminate()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed:
            return True, "프로그램이 종료되었습니다."
        else:
            return False, "실행 중인 프로그램을 찾을 수 없습니다."
    except Exception as e:
        return False, f"종료 실패: {str(e)}"


def restart_program(program_path, args=""):
    """프로그램 재시작.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        args: 실행 인자 (선택사항)
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    stop_program(program_path)
    import time
    time.sleep(1)  # 종료 대기
    return start_program(program_path, args)


def get_process_stats(program_path):
    """프로그램의 CPU 및 메모리 사용량 조회.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        
    Returns:
        dict: {
            'cpu_percent': CPU 사용률 (0-100),
            'memory_mb': 메모리 사용량 (MB),
            'memory_percent': 메모리 사용률 (0-100),
            'running': 실행 여부
        }
    """
    try:
        program_name = Path(program_path).name
        
        for proc in psutil.process_iter(['name', 'exe', 'cpu_percent', 'memory_info']):
            try:
                if proc.info['exe'] and Path(proc.info['exe']).name.lower() == program_name.lower():
                    # CPU 사용률 계산 (interval=0.1초로 측정)
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    
                    # 메모리 사용량 (MB 단위)
                    memory_info = proc.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)  # bytes to MB
                    
                    # 메모리 사용률
                    memory_percent = proc.memory_percent()
                    
                    return {
                        'cpu_percent': round(cpu_percent, 2),
                        'memory_mb': round(memory_mb, 2),
                        'memory_percent': round(memory_percent, 2),
                        'running': True
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 프로세스를 찾지 못한 경우
        return {
            'cpu_percent': 0,
            'memory_mb': 0,
            'memory_percent': 0,
            'running': False
        }
    except Exception:
        return {
            'cpu_percent': 0,
            'memory_mb': 0,
            'memory_percent': 0,
            'running': False
        }
