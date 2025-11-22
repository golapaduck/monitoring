"""PowerShell 기반 네트워크 정보."""

import logging
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)


def get_network_info() -> Dict[str, Any]:
    """네트워크 정보 조회 (PowerShell 사용).
    
    Returns:
        네트워크 정보 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: 네트워크 정보 JSON으로 반환
        script = """
        Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, IPv4DefaultGateway, DNSServer | ConvertTo-Json
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
                logger.info("네트워크 정보 조회 성공 (PowerShell)")
                return {"interfaces": info if isinstance(info, list) else [info]}
            except json.JSONDecodeError as e:
                logger.warning(f"PowerShell 결과 파싱 오류: {str(e)}")
                return {}
        else:
            logger.warning(f"PowerShell 네트워크 정보 조회 실패: {command.error}")
            return {}
    
    except Exception as e:
        logger.error(f"네트워크 정보 조회 오류: {str(e)}")
        return {}


def get_ip_address() -> Dict[str, List[str]]:
    """IP 주소 조회 (PowerShell 사용).
    
    Returns:
        IP 주소 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: IP 주소 조회
        script = """
        Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress, InterfaceAlias | ConvertTo-Json
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
                ips = json.loads(command.output)
                logger.info("IP 주소 조회 성공 (PowerShell)")
                return {"ipv4_addresses": ips if isinstance(ips, list) else [ips]}
            except json.JSONDecodeError:
                return {}
        else:
            return {}
    
    except Exception as e:
        logger.error(f"IP 주소 조회 오류: {str(e)}")
        return {}


def test_connection(hostname: str, timeout: int = 5) -> Dict[str, Any]:
    """호스트 연결 테스트 (PowerShell 사용).
    
    Args:
        hostname: 테스트할 호스트명 또는 IP
        timeout: 타임아웃 (초)
        
    Returns:
        연결 테스트 결과 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: Ping 테스트
        script = f"""
        $result = Test-Connection -ComputerName "{hostname}" -Count 1 -ErrorAction SilentlyContinue
        if ($result) {{
            @{{
                Success = $true
                Hostname = $result.PSComputerName
                ResponseTime = $result.ResponseTime
                TTL = $result.Reply.Status
            }} | ConvertTo-Json
        }} else {{
            @{{
                Success = $false
                Hostname = "{hostname}"
                Error = "호스트에 연결할 수 없습니다"
            }} | ConvertTo-Json
        }}
        """
        
        command_id = agent.execute(script, timeout=timeout + 5)
        command = agent.get_command(command_id)
        
        # 명령 완료 대기
        import time
        for _ in range((timeout + 5) * 10):
            if command.completed_at:
                break
            time.sleep(0.1)
        
        if command.output:
            try:
                result = json.loads(command.output)
                logger.info(f"연결 테스트 완료: {hostname}")
                return result
            except json.JSONDecodeError:
                return {"success": False, "error": "결과 파싱 실패"}
        else:
            return {"success": False, "error": command.error or "알 수 없는 오류"}
    
    except Exception as e:
        logger.error(f"연결 테스트 오류: {str(e)}")
        return {"success": False, "error": str(e)}


def get_dns_servers() -> Dict[str, List[str]]:
    """DNS 서버 조회 (PowerShell 사용).
    
    Returns:
        DNS 서버 정보 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: DNS 서버 조회
        script = """
        Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, ServerAddresses | ConvertTo-Json
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
                dns_info = json.loads(command.output)
                logger.info("DNS 서버 조회 성공 (PowerShell)")
                return {"dns_servers": dns_info if isinstance(dns_info, list) else [dns_info]}
            except json.JSONDecodeError:
                return {}
        else:
            return {}
    
    except Exception as e:
        logger.error(f"DNS 서버 조회 오류: {str(e)}")
        return {}


def get_network_statistics() -> Dict[str, Any]:
    """네트워크 통계 조회 (PowerShell 사용).
    
    Returns:
        네트워크 통계 딕셔너리
    """
    try:
        from utils.powershell_agent import get_powershell_agent
        agent = get_powershell_agent()
        
        # PowerShell 스크립트: 네트워크 통계
        script = """
        $stats = Get-NetAdapterStatistics
        @{
            Adapters = @($stats | Select-Object Name, ReceivedBytes, SentBytes, ReceivedUnicastPackets, SentUnicastPackets)
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
                stats = json.loads(command.output)
                logger.info("네트워크 통계 조회 성공 (PowerShell)")
                return stats
            except json.JSONDecodeError:
                return {}
        else:
            return {}
    
    except Exception as e:
        logger.error(f"네트워크 통계 조회 오류: {str(e)}")
        return {}
