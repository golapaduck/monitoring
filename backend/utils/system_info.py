"""시스템 정보 수집 (PowerShell 기반)."""

import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


def get_system_info() -> Dict[str, Any]:
    """시스템 정보 조회 (PowerShell 사용).
    
    Returns:
        시스템 정보 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: 시스템 정보 JSON으로 반환
        script = """
        @{
            ComputerName = $env:COMPUTERNAME
            OSVersion = [System.Environment]::OSVersion.VersionString
            ProcessorCount = (Get-WmiObject Win32_ComputerSystem).NumberOfProcessors
            TotalMemory = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
            AvailableMemory = [math]::Round((Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
            SystemUptime = (Get-Date) - (Get-WmiObject Win32_OperatingSystem).LastBootUpTime
        } | ConvertTo-Json
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
                logger.info("시스템 정보 조회 성공 (PowerShell)")
                return info
            except json.JSONDecodeError as e:
                logger.warning(f"PowerShell 결과 파싱 오류: {str(e)}")
                return _get_system_info_psutil()
        else:
            logger.warning(f"PowerShell 시스템 정보 조회 실패: {command.error}")
            return _get_system_info_psutil()
    
    except RuntimeError:
        # 에이전트 미초기화 시 psutil 사용
        logger.debug("PowerShell 에이전트 미초기화, psutil 사용")
        return _get_system_info_psutil()
    except Exception as e:
        logger.error(f"시스템 정보 조회 오류: {str(e)}")
        return _get_system_info_psutil()


def get_cpu_info() -> Dict[str, Any]:
    """CPU 정보 조회 (PowerShell 사용).
    
    Returns:
        CPU 정보 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: CPU 정보 JSON으로 반환
        script = """
        @{
            ProcessorCount = (Get-WmiObject Win32_ComputerSystem).NumberOfProcessors
            ProcessorName = (Get-WmiObject Win32_Processor)[0].Name
            MaxClockSpeed = (Get-WmiObject Win32_Processor)[0].MaxClockSpeed
            CurrentClockSpeed = (Get-WmiObject Win32_Processor)[0].CurrentClockSpeed
        } | ConvertTo-Json
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
                logger.info("CPU 정보 조회 성공 (PowerShell)")
                return info
            except json.JSONDecodeError:
                return {}
        else:
            return {}
    
    except Exception as e:
        logger.error(f"CPU 정보 조회 오류: {str(e)}")
        return {}


def get_memory_info() -> Dict[str, Any]:
    """메모리 정보 조회 (PowerShell 사용).
    
    Returns:
        메모리 정보 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: 메모리 정보 JSON으로 반환
        script = """
        @{
            TotalMemory = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
            AvailableMemory = [math]::Round((Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
            UsedMemory = [math]::Round(((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory - (Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory) / 1GB, 2)
            MemoryUsagePercent = [math]::Round(((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory - (Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory) / (Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory * 100, 2)
        } | ConvertTo-Json
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
                logger.info("메모리 정보 조회 성공 (PowerShell)")
                return info
            except json.JSONDecodeError:
                return {}
        else:
            return {}
    
    except Exception as e:
        logger.error(f"메모리 정보 조회 오류: {str(e)}")
        return {}


def _get_system_info_psutil() -> Dict[str, Any]:
    """psutil을 사용한 시스템 정보 조회 (폴백).
    
    Returns:
        시스템 정보 딕셔너리
    """
    try:
        import psutil
        import socket
        from datetime import datetime, timedelta
        
        # 부팅 시간 계산
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            "ComputerName": socket.gethostname(),
            "OSVersion": f"{psutil.os.uname().system} {psutil.os.uname().release}",
            "ProcessorCount": psutil.cpu_count(),
            "TotalMemory": round(psutil.virtual_memory().total / (1024**3), 2),
            "AvailableMemory": round(psutil.virtual_memory().available / (1024**2), 2),
            "SystemUptime": str(uptime)
        }
    except Exception as e:
        logger.error(f"psutil 시스템 정보 조회 오류: {str(e)}")
        return {}
