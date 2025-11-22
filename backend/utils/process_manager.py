"""프로세스 관리 유틸리티 함수들."""

import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import psutil


def get_process_status(program_path: str, pid: Optional[int] = None) -> Tuple[bool, Optional[int]]:
    """프로그램 경로로 프로세스 실행 여부 확인 (더블 체크: PID + 이름).
    
    PID와 프로세스 이름을 모두 검증하여 정확성을 높입니다.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        pid: 프로세스 ID (선택사항)
        
    Returns:
        tuple: (실행 여부, 현재 PID 또는 None)
    """
    try:
        program_name = Path(program_path).name.lower()
        
        # 1단계: PID가 제공된 경우 PID + 이름 더블 체크
        if pid is not None:
            try:
                proc = psutil.Process(pid)
                
                # 프로세스가 존재하고 실행 중인지 확인
                if not proc.is_running():
                    # PID는 존재하지만 실행 중이 아니면 2단계로
                    return _find_by_name(program_name)
                
                # 더블 체크: PID + 프로세스 이름 검증
                try:
                    proc_name = proc.name().lower()
                    proc_exe = proc.exe()
                    
                    # 이름 일치 확인
                    if proc_name == program_name:
                        return True, pid
                    
                    # 전체 경로로도 확인
                    if proc_exe and Path(proc_exe).name.lower() == program_name:
                        return True, pid
                    
                    # PID는 존재하지만 이름이 다름 (프로세스 재사용 가능성)
                    return _find_by_name(program_name)
                    
                except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
                    print(f"⚠️ [Process Manager] PID {pid} 접근 거부 또는 없음: {str(e)}")
                    # 권한 문제 또는 프로세스 사라짐 - 2단계로
                    return _find_by_name(program_name)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"⚠️ [Process Manager] PID {pid} 확인 실패: {str(e)}")
                # PID로 프로세스를 찾을 수 없으면 2단계로
                return _find_by_name(program_name)
        
        # 2단계: PID가 없거나 검증 실패 시 이름으로 검색
        return _find_by_name(program_name)
        
    except Exception as e:
        print(f"⚠️ [Process Manager] 프로세스 상태 확인 오류: {str(e)}")
        return False, None


def _find_by_name(program_name: str) -> Tuple[bool, Optional[int]]:
    """프로세스 이름으로 검색 (내부 헬퍼 함수).
    
    Args:
        program_name: 프로그램 이름 (소문자)
        
    Returns:
        tuple: (실행 여부, PID 또는 None)
    """
    try:
        for proc in psutil.process_iter(['name', 'exe', 'pid']):
            try:
                # 프로세스 이름으로 비교
                if proc.info['name'] and proc.info['name'].lower() == program_name:
                    return True, proc.info['pid']
                
                # 실행 파일 경로로도 비교 (더 정확함)
                if proc.info['exe'] and Path(proc.info['exe']).name.lower() == program_name:
                    return True, proc.info['pid']
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False, None
        
    except Exception as e:
        print(f"⚠️ [Process Manager] 이름 검색 오류: {str(e)}")
        return False, None


def get_programs_status_batch(programs: List[Dict]) -> List[Dict]:
    """여러 프로그램의 상태를 한 번에 조회 (배치 처리 - PowerShell 사용).
    
    PowerShell Get-Process를 사용하여 성능을 향상시킵니다.
    
    Args:
        programs: 프로그램 목록 (dict 리스트)
        
    Returns:
        list: 상태가 추가된 프로그램 목록
    """
    # 1단계: PowerShell로 모든 프로세스 정보 수집
    running_processes = {}
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: 모든 프로세스 정보 JSON으로 반환
        script = """
        Get-Process | Select-Object Name, Id, Path | ConvertTo-Json
        """
        
        command_id = agent.execute(script, timeout=10)
        command = agent.get_command(command_id)
        
        # 명령 완료 대기
        import time
        for _ in range(100):
            if command.completed_at:
                break
            time.sleep(0.1)
        
        if command.result and command.output:
            import json
            try:
                processes = json.loads(command.output)
                if not isinstance(processes, list):
                    processes = [processes]
                
                for proc in processes:
                    name = proc.get('Name', '').lower()
                    pid = proc.get('Id')
                    if name and pid:
                        running_processes[name] = pid
                        # exe 이름으로도 저장
                        if proc.get('Path'):
                            exe_name = Path(proc['Path']).name.lower()
                            if exe_name not in running_processes:
                                running_processes[exe_name] = pid
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ [Process Manager] PowerShell 결과 파싱 오류: {str(e)}")
                # 폴백: psutil 사용
                running_processes = _get_processes_psutil()
    
    except RuntimeError:
        # 에이전트 미초기화 시 psutil 사용
        running_processes = _get_processes_psutil()
    except Exception as e:
        print(f"⚠️ [Process Manager] PowerShell 프로세스 조회 오류: {str(e)}")
        running_processes = _get_processes_psutil()
    
    # 2단계: 각 프로그램의 상태 확인
    result = []
    for program in programs:
        try:
            program_name = Path(program['path']).name.lower()
            
            # 실행 중인 프로세스에서 찾기
            pid = running_processes.get(program_name)
            
            # PID 더블 체크 (저장된 PID가 있는 경우)
            if program.get('pid') and not pid:
                # 저장된 PID로 확인
                try:
                    proc = psutil.Process(program['pid'])
                    if proc.is_running():
                        proc_name = proc.name().lower()
                        if proc_name == program_name:
                            pid = program['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            result.append({
                **program,
                'running': pid is not None,
                'pid': pid
            })
            
        except Exception as e:
            print(f"⚠️ [Process Manager] 프로그램 상태 확인 오류 ({program.get('name', 'Unknown')}): {str(e)}")
            result.append({
                **program,
                'running': False,
                'pid': None
            })
    
    return result


def _get_processes_psutil() -> Dict[str, int]:
    """psutil을 사용한 프로세스 정보 수집 (폴백).
    
    Returns:
        프로세스 이름 -> PID 딕셔너리
    """
    running_processes = {}
    try:
        for proc in psutil.process_iter(['name', 'exe', 'pid']):
            try:
                if proc.info['name']:
                    name = proc.info['name'].lower()
                    running_processes[name] = proc.info['pid']
                
                if proc.info['exe']:
                    exe_name = Path(proc.info['exe']).name.lower()
                    if exe_name not in running_processes:
                        running_processes[exe_name] = proc.info['pid']
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"⚠️ [Process Manager] psutil 프로세스 조회 오류: {str(e)}")
    
    return running_processes


def start_program(program_path: str, args: str = "") -> Tuple[bool, str, Optional[int]]:
    """프로그램 실행 (PowerShell 에이전트 사용).
    
    Args:
        program_path: 프로그램 실행 파일 경로
        args: 실행 인자 (선택사항)
        
    Returns:
        tuple: (성공 여부, 메시지, PID 또는 None)
    """
    try:
        # PowerShell 에이전트 사용
        try:
            from utils.powershell_agent import get_powershell_agent
            agent = get_powershell_agent()
            
            # PowerShell 스크립트 생성
            cmd = f'"{program_path}"'
            if args:
                cmd += f' {args}'
            
            script = f'Start-Process -FilePath {cmd} -WindowStyle Hidden'
            agent.execute(script, timeout=10)
            
            # 프로세스 시작 후 PID 찾기
            import time
            time.sleep(0.5)
            
            is_running, pid = get_process_status(program_path)
            if is_running and pid:
                return True, "프로그램이 실행되었습니다.", pid
            else:
                return True, "프로그램이 실행되었습니다. (PID 확인 불가)", None
        
        except RuntimeError:
            # 에이전트 미초기화 시 직접 실행
            cmd = f'"{program_path}"'
            if args:
                cmd += f" {args}"
            
            subprocess.Popen(
                ["powershell", "-Command", f"Start-Process -FilePath {cmd}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            import time
            time.sleep(0.5)
            
            is_running, pid = get_process_status(program_path)
            if is_running and pid:
                return True, "프로그램이 실행되었습니다.", pid
            else:
                return True, "프로그램이 실행되었습니다. (PID 확인 불가)", None
    
    except Exception as e:
        return False, f"실행 실패: {str(e)}", None


def stop_program(program_path: str, force: bool = False) -> Tuple[bool, str]:
    """프로그램 종료 (psutil 사용).
    
    Args:
        program_path: 프로그램 실행 파일 경로
        force: True이면 자식 프로세스까지 강제 종료
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        program_name = Path(program_path).name
        print(f"🔸 [Process Manager] 프로그램 종료 시작: {program_name}")
        
        # psutil을 직접 사용 (더 안정적)
        success, message = _stop_with_psutil(program_path, force)
        
        if success:
            print(f"✅ [Process Manager] 종료 성공: {program_name}")
        else:
            print(f"❌ [Process Manager] 종료 실패: {program_name}")
        
        return success, message
            
    except Exception as e:
        print(f"💥 [Process Manager] 종료 중 예외 발생: {str(e)}")
        return False, f"종료 실패: {str(e)}"


def _stop_with_psutil(program_path: str, force: bool = False) -> Tuple[bool, str]:
    """psutil을 사용한 프로그램 종료.
    
    자식 프로세스까지 모두 종료합니다.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        force: True이면 강제 종료
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        program_name = Path(program_path).name
        program_stem = Path(program_name).stem.lower()
        killed_count = 0
        processes_to_kill = []
        
        print(f"🔍 [Process Manager] 프로세스 검색: {program_name} (stem: {program_stem})")
        
        # 1단계: 대상 프로세스 찾기 (exe 경로와 프로세스 이름 모두 확인)
        for proc in psutil.process_iter(['name', 'exe', 'pid']):
            try:
                proc_name = proc.info['name'].lower()
                proc_exe = proc.info['exe']
                
                # 프로세스 이름으로 매칭 (app.exe -> app)
                if proc_name == program_stem + '.exe' or proc_name == program_stem:
                    processes_to_kill.append(proc)
                    print(f"✓ [Process Manager] 프로세스 발견: {proc.info['name']} (PID: {proc.pid})")
                # exe 경로로도 매칭
                elif proc_exe and Path(proc_exe).name.lower() == program_name.lower():
                    processes_to_kill.append(proc)
                    print(f"✓ [Process Manager] 프로세스 발견 (경로): {proc.info['name']} (PID: {proc.pid})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                continue
        
        if not processes_to_kill:
            # 프로세스를 찾을 수 없음 (이미 종료됨)
            print(f"ℹ️ [Process Manager] 실행 중인 프로세스 없음: {program_name}")
            return True, "프로그램이 이미 종료되었습니다."
        
        print(f"📊 [Process Manager] 종료 대상: {len(processes_to_kill)}개 프로세스")
        
        # 2단계: 각 프로세스와 자식 프로세스 종료
        for proc in processes_to_kill:
            try:
                if not proc.is_running():
                    print(f"ℹ️ [Process Manager] 이미 종료됨: {proc.name()} (PID: {proc.pid})")
                    killed_count += 1
                    continue
                
                # 자식 프로세스 찾기
                try:
                    children = proc.children(recursive=True)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    children = []
                
                # 먼저 자식 프로세스 종료
                for child in children:
                    try:
                        if child.is_running():
                            print(f"🔹 [Process Manager] 자식 프로세스 종료: {child.name()} (PID: {child.pid})")
                            if force:
                                child.kill()
                            else:
                                child.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # 부모 프로세스 종료
                if proc.is_running():
                    print(f"🔸 [Process Manager] 부모 프로세스 종료: {proc.name()} (PID: {proc.pid})")
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    
                    # 종료 대기 (최대 3초)
                    try:
                        proc.wait(timeout=3)
                        print(f"✅ [Process Manager] 프로세스 종료 완료: {proc.name()} (PID: {proc.pid})")
                        killed_count += 1
                    except psutil.TimeoutExpired:
                        # 강제 종료
                        print(f"⚠️ [Process Manager] 타임아웃 - 강제 종료: {proc.name()} (PID: {proc.pid})")
                        proc.kill()
                        try:
                            proc.wait(timeout=1)
                            killed_count += 1
                        except psutil.TimeoutExpired:
                            print(f"❌ [Process Manager] 강제 종료 실패: {proc.name()} (PID: {proc.pid})")
                        
                        # 자식 프로세스도 강제 종료
                        for child in children:
                            try:
                                if child.is_running():
                                    child.kill()
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"⚠️ [Process Manager] 프로세스 접근 오류: {str(e)}")
                continue
            except Exception as e:
                print(f"⚠️ [Process Manager] 프로세스 종료 중 오류: {str(e)}")
                continue
        
        if killed_count > 0:
            return True, f"프로그램이 종료되었습니다. ({killed_count}개 프로세스)"
        else:
            # 프로그램이 실행 중이 아니면 성공으로 처리
            return True, "프로그램이 이미 종료되었습니다."
    except Exception as e:
        print(f"💥 [Process Manager] psutil 종료 오류: {str(e)}")
        import traceback
        traceback.print_exc()
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
