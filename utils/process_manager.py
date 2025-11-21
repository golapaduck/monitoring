"""프로세스 관리 유틸리티 함수들."""

import subprocess
from pathlib import Path
import psutil


def get_process_status(program_path, pid=None):
    """프로그램 경로로 프로세스 실행 여부 확인.
    
    PID가 제공되면 먼저 PID로 확인하고, 없으면 프로그램 이름으로 확인합니다.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        pid: 프로세스 ID (선택사항)
        
    Returns:
        tuple: (실행 여부, 현재 PID 또는 None)
    """
    try:
        # 1단계: PID가 제공된 경우 먼저 PID로 확인
        if pid is not None:
            try:
                proc = psutil.Process(pid)
                # 프로세스가 존재하고 실행 중인지 확인
                if proc.is_running():
                    # 프로그램 경로가 일치하는지 확인
                    try:
                        proc_exe = proc.exe()
                        if proc_exe and Path(proc_exe).name.lower() == Path(program_path).name.lower():
                            return True, pid
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        # 권한 문제로 경로를 확인할 수 없는 경우, 이름만으로 확인
                        if proc.name().lower() == Path(program_path).name.lower():
                            return True, pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # PID로 프로세스를 찾을 수 없으면 2단계로 진행
                pass
        
        # 2단계: 프로그램 이름으로 검색
        program_name = Path(program_path).name
        for proc in psutil.process_iter(['name', 'exe', 'pid']):
            try:
                # 실행 파일 경로로 비교 (더 정확함)
                if proc.info['exe'] and Path(proc.info['exe']).name.lower() == program_name.lower():
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False, None
    except Exception as e:
        print(f"⚠️ [Process Manager] 프로세스 상태 확인 오류: {str(e)}")
        return False, None


def start_program(program_path, args=""):
    """프로그램 실행.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        args: 실행 인자 (선택사항)
        
    Returns:
        tuple: (성공 여부, 메시지, PID 또는 None)
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
        
        # 프로세스 시작 후 PID 찾기 (약간의 지연 후)
        import time
        time.sleep(0.5)  # 프로세스 시작 대기
        
        is_running, pid = get_process_status(program_path)
        if is_running and pid:
            return True, "프로그램이 실행되었습니다.", pid
        else:
            return True, "프로그램이 실행되었습니다. (PID 확인 불가)", None
    except Exception as e:
        return False, f"실행 실패: {str(e)}", None


def stop_program(program_path, force=False):
    """프로그램 종료.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        force: True이면 자식 프로세스까지 강제 종료 (taskkill /T 사용)
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        program_name = Path(program_path).name
        
        if force:
            # Windows taskkill 명령어로 자식 프로세스까지 강제 종료
            # /F: 강제 종료, /T: 자식 프로세스 트리 종료, /IM: 이미지 이름
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/T", "/IM", program_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print(f"✅ [Process Manager] 강제 종료 성공: {program_name}")
                    return True, "프로그램과 모든 자식 프로세스가 강제 종료되었습니다."
                elif result.returncode == 128:
                    # 프로세스를 찾을 수 없음 (이미 종료됨)
                    print(f"ℹ️ [Process Manager] 프로세스가 이미 종료됨: {program_name}")
                    return True, "프로그램이 이미 종료되었습니다."
                else:
                    # taskkill 실패 시 psutil로 시도
                    print(f"⚠️ [Process Manager] taskkill 실패, psutil로 재시도: {program_name}")
                    return _stop_with_psutil(program_path)
            except subprocess.TimeoutExpired:
                return False, "종료 명령 시간 초과"
            except Exception as e:
                print(f"⚠️ [Process Manager] taskkill 오류, psutil로 재시도: {str(e)}")
                return _stop_with_psutil(program_path)
        else:
            # 일반 종료 (psutil 사용)
            return _stop_with_psutil(program_path)
            
    except Exception as e:
        return False, f"종료 실패: {str(e)}"


def _stop_with_psutil(program_path):
    """psutil을 사용한 프로그램 종료 (내부 함수).
    
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
            # 프로그램이 실행 중이 아니면 성공으로 처리
            return True, "프로그램이 이미 종료되었습니다."
    except Exception as e:
        return False, f"종료 실패: {str(e)}"


def restart_program(program_path, args=""):
    """프로그램 재시작.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        args: 실행 인자 (선택사항)
        
    Returns:
        tuple: (성공 여부, 메시지, PID 또는 None)
    """
    stop_program(program_path)
    import time
    time.sleep(1)  # 종료 대기
    return start_program(program_path, args)


def get_process_stats(program_path, pid=None):
    """프로그램의 CPU 및 메모리 사용량 조회.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        pid: 프로세스 ID (선택사항)
        
    Returns:
        dict: {
            'cpu_percent': CPU 사용률 (0-100),
            'memory_mb': 메모리 사용량 (MB),
            'memory_percent': 메모리 사용률 (0-100),
            'running': 실행 여부,
            'pid': 프로세스 ID (실행 중인 경우)
        }
    """
    try:
        # PID가 제공된 경우 먼저 PID로 확인
        if pid is not None:
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    # CPU 사용률 계산
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    
                    # 메모리 사용량 (MB 단위)
                    memory_info = proc.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    
                    # 메모리 사용률
                    memory_percent = proc.memory_percent()
                    
                    return {
                        'cpu_percent': round(cpu_percent, 2),
                        'memory_mb': round(memory_mb, 2),
                        'memory_percent': round(memory_percent, 2),
                        'running': True,
                        'pid': pid
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 프로그램 이름으로 검색
        program_name = Path(program_path).name
        
        for proc in psutil.process_iter(['name', 'exe', 'cpu_percent', 'memory_info', 'pid']):
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
                        'running': True,
                        'pid': proc.info['pid']
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 프로세스를 찾지 못한 경우
        return {
            'cpu_percent': 0,
            'memory_mb': 0,
            'memory_percent': 0,
            'running': False,
            'pid': None
        }
    except Exception:
        return {
            'cpu_percent': 0,
            'memory_mb': 0,
            'memory_percent': 0,
            'running': False,
            'pid': None
        }
