"""PowerShell 기반 파일 작업."""

import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def copy_file(source: str, destination: str, recursive: bool = False) -> Tuple[bool, str]:
    """파일/디렉토리 복사 (PowerShell 사용).
    
    Args:
        source: 원본 경로
        destination: 대상 경로
        recursive: True이면 디렉토리 재귀 복사
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트
        if recursive:
            script = f'Copy-Item -Path "{source}" -Destination "{destination}" -Recurse -Force'
        else:
            script = f'Copy-Item -Path "{source}" -Destination "{destination}" -Force'
        
        command_id = agent.execute(script, timeout=30)
        command = agent.get_command(command_id)
        
        # 명령 완료 대기
        import time
        for _ in range(300):
            if command.completed_at:
                break
            time.sleep(0.1)
        
        if command.result:
            msg = f"파일 복사 성공: {source} → {destination}"
            logger.info(msg)
            return True, msg
        else:
            msg = f"파일 복사 실패: {command.error}"
            logger.error(msg)
            return False, msg
    
    except Exception as e:
        msg = f"파일 복사 오류: {str(e)}"
        logger.error(msg)
        return False, msg


def move_file(source: str, destination: str) -> Tuple[bool, str]:
    """파일/디렉토리 이동 (PowerShell 사용).
    
    Args:
        source: 원본 경로
        destination: 대상 경로
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트
        script = f'Move-Item -Path "{source}" -Destination "{destination}" -Force'
        
        command_id = agent.execute(script, timeout=30)
        command = agent.get_command(command_id)
        
        # 명령 완료 대기
        import time
        for _ in range(300):
            if command.completed_at:
                break
            time.sleep(0.1)
        
        if command.result:
            msg = f"파일 이동 성공: {source} → {destination}"
            logger.info(msg)
            return True, msg
        else:
            msg = f"파일 이동 실패: {command.error}"
            logger.error(msg)
            return False, msg
    
    except Exception as e:
        msg = f"파일 이동 오류: {str(e)}"
        logger.error(msg)
        return False, msg


def delete_file(path: str, recursive: bool = False) -> Tuple[bool, str]:
    """파일/디렉토리 삭제 (PowerShell 사용).
    
    Args:
        path: 삭제할 경로
        recursive: True이면 디렉토리 재귀 삭제
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트
        if recursive:
            script = f'Remove-Item -Path "{path}" -Recurse -Force'
        else:
            script = f'Remove-Item -Path "{path}" -Force'
        
        command_id = agent.execute(script, timeout=30)
        command = agent.get_command(command_id)
        
        # 명령 완료 대기
        import time
        for _ in range(300):
            if command.completed_at:
                break
            time.sleep(0.1)
        
        if command.result:
            msg = f"파일 삭제 성공: {path}"
            logger.info(msg)
            return True, msg
        else:
            msg = f"파일 삭제 실패: {command.error}"
            logger.error(msg)
            return False, msg
    
    except Exception as e:
        msg = f"파일 삭제 오류: {str(e)}"
        logger.error(msg)
        return False, msg


def create_directory(path: str) -> Tuple[bool, str]:
    """디렉토리 생성 (PowerShell 사용).
    
    Args:
        path: 생성할 디렉토리 경로
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트
        script = f'New-Item -ItemType Directory -Path "{path}" -Force | Out-Null'
        
        command_id = agent.execute(script, timeout=10)
        command = agent.get_command(command_id)
        
        # 명령 완료 대기
        import time
        for _ in range(100):
            if command.completed_at:
                break
            time.sleep(0.1)
        
        if command.result:
            msg = f"디렉토리 생성 성공: {path}"
            logger.info(msg)
            return True, msg
        else:
            msg = f"디렉토리 생성 실패: {command.error}"
            logger.error(msg)
            return False, msg
    
    except Exception as e:
        msg = f"디렉토리 생성 오류: {str(e)}"
        logger.error(msg)
        return False, msg


def get_file_info(path: str) -> dict:
    """파일 정보 조회 (PowerShell 사용).
    
    Args:
        path: 파일 경로
        
    Returns:
        파일 정보 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        import json
        
        agent = get_powershell_agent()
        
        # PowerShell 스크립트
        script = f"""
        Get-Item -Path "{path}" | Select-Object Name, FullName, Length, CreationTime, LastWriteTime | ConvertTo-Json
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
            try:
                info = json.loads(command.output)
                logger.info(f"파일 정보 조회 성공: {path}")
                return info
            except json.JSONDecodeError:
                return {}
        else:
            logger.warning(f"파일 정보 조회 실패: {command.error}")
            return {}
    
    except Exception as e:
        logger.error(f"파일 정보 조회 오류: {str(e)}")
        return {}
