"""PowerShell 에이전트 API 엔드포인트."""

from flask import Blueprint, request, jsonify
import logging
from utils.powershell_agent import get_powershell_agent
from utils.decorators import require_auth, require_admin

logger = logging.getLogger(__name__)

# Blueprint 생성
powershell_api = Blueprint('powershell_api', __name__, url_prefix='/api/powershell')


@powershell_api.route("/execute", methods=["POST"])
@require_auth
@require_admin
def execute_command():
    """PowerShell 명령 실행 API.
    
    Request:
        {
            "script": "Get-Process",
            "timeout": 30
        }
    """
    try:
        data = request.get_json()
        
        if not data.get("script"):
            return jsonify({
                "error": "script 필드가 필요합니다"
            }), 400
        
        script = data["script"]
        timeout = data.get("timeout", 30)
        
        # 타임아웃 범위 검증 (최대 300초)
        if timeout > 300:
            timeout = 300
        
        agent = get_powershell_agent()
        command_id = agent.execute(script, timeout)
        
        logger.info(f"PowerShell 명령 실행: {command_id}")
        
        return jsonify({
            "command_id": command_id,
            "message": "명령이 실행 중입니다"
        }), 202
    
    except Exception as e:
        logger.error(f"PowerShell 명령 실행 실패: {str(e)}")
        return jsonify({
            "error": "명령 실행 실패",
            "message": str(e)
        }), 500


@powershell_api.route("/commands", methods=["GET"])
@require_auth
@require_admin
def list_commands():
    """모든 PowerShell 명령 조회 API."""
    try:
        agent = get_powershell_agent()
        commands = agent.get_all_commands()
        
        return jsonify({
            "commands": commands,
            "total": len(commands)
        })
    
    except Exception as e:
        logger.error(f"명령 목록 조회 실패: {str(e)}")
        return jsonify({
            "error": "명령 목록 조회 실패",
            "message": str(e)
        }), 500


@powershell_api.route("/commands/<command_id>", methods=["GET"])
@require_auth
@require_admin
def get_command(command_id):
    """특정 PowerShell 명령 조회 API.
    
    Args:
        command_id: 명령 ID
    """
    try:
        agent = get_powershell_agent()
        command = agent.get_command(command_id)
        
        if not command:
            return jsonify({
                "error": "명령을 찾을 수 없습니다"
            }), 404
        
        return jsonify(command.to_dict())
    
    except Exception as e:
        logger.error(f"명령 조회 실패: {str(e)}")
        return jsonify({
            "error": "명령 조회 실패",
            "message": str(e)
        }), 500


@powershell_api.route("/process/list", methods=["GET"])
@require_auth
def list_processes():
    """프로세스 목록 조회 API (PowerShell 사용)."""
    try:
        agent = get_powershell_agent()
        
        # PowerShell 스크립트로 프로세스 목록 조회
        script = """
        Get-Process | Select-Object Name, Id, WorkingSet, CPU | ConvertTo-Json
        """
        
        command_id = agent.execute(script, timeout=10)
        command = agent.get_command(command_id)
        
        # 명령 완료 대기 (최대 10초)
        import time
        for _ in range(100):
            if command.completed_at:
                break
            time.sleep(0.1)
        
        if command.result and command.output:
            import json
            try:
                processes = json.loads(command.output)
                return jsonify({
                    "processes": processes if isinstance(processes, list) else [processes],
                    "total": len(processes) if isinstance(processes, list) else 1
                })
            except json.JSONDecodeError:
                return jsonify({
                    "output": command.output,
                    "total": 0
                })
        else:
            return jsonify({
                "error": command.error or "프로세스 목록 조회 실패",
                "command_id": command_id
            }), 500
    
    except Exception as e:
        logger.error(f"프로세스 목록 조회 실패: {str(e)}")
        return jsonify({
            "error": "프로세스 목록 조회 실패",
            "message": str(e)
        }), 500


@powershell_api.route("/system/info", methods=["GET"])
@require_auth
def get_system_info():
    """시스템 정보 조회 API (PowerShell 사용)."""
    try:
        agent = get_powershell_agent()
        
        # PowerShell 스크립트로 시스템 정보 조회
        script = """
        @{
            ComputerName = $env:COMPUTERNAME
            OSVersion = [System.Environment]::OSVersion.VersionString
            ProcessorCount = (Get-WmiObject Win32_ComputerSystem).NumberOfProcessors
            TotalMemory = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
            AvailableMemory = [math]::Round((Get-WmiObject Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
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
            import json
            try:
                info = json.loads(command.output)
                return jsonify(info)
            except json.JSONDecodeError:
                return jsonify({
                    "output": command.output
                })
        else:
            return jsonify({
                "error": command.error or "시스템 정보 조회 실패",
                "command_id": command_id
            }), 500
    
    except Exception as e:
        logger.error(f"시스템 정보 조회 실패: {str(e)}")
        return jsonify({
            "error": "시스템 정보 조회 실패",
            "message": str(e)
        }), 500
