"""시스템 상태 조회 API 엔드포인트 (향후 확장용)."""

from flask import Blueprint, session, jsonify
from datetime import datetime

# Blueprint 생성
status_api = Blueprint('status_api', __name__, url_prefix='/api/status')

# 설정 및 유틸리티 임포트
from utils.database import get_all_programs
from utils.process_manager import get_process_status


@status_api.route("", methods=["GET"])
def get_status():
    """프로그램 상태 조회 API (기본 엔드포인트) - 최적화됨."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # 데이터베이스에서 직접 조회 (JSON 파일 읽기 제거)
    programs = get_all_programs()
    
    # 프로그램 상태 확인
    status_list = []
    for program in programs:
        is_running, current_pid = get_process_status(
            program["path"], 
            pid=program.get("pid")
        )
        
        status_list.append({
            **program,
            "running": is_running,
            "pid": current_pid
        })
    
    return jsonify({
        "last_update": datetime.now().isoformat(),
        "programs_status": status_list
    })


# 향후 확장 가능한 엔드포인트들
@status_api.route("/system", methods=["GET"])
def get_system_status():
    """시스템 리소스 상태 조회 (CPU, 메모리, 디스크 등)."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    import psutil
    
    # CPU 정보
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # 메모리 정보
    memory = psutil.virtual_memory()
    memory_total_gb = memory.total / (1024 ** 3)
    memory_used_gb = memory.used / (1024 ** 3)
    memory_available_gb = memory.available / (1024 ** 3)
    
    # 디스크 정보
    disk = psutil.disk_usage('/')
    disk_total_gb = disk.total / (1024 ** 3)
    disk_used_gb = disk.used / (1024 ** 3)
    disk_free_gb = disk.free / (1024 ** 3)
    
    # 네트워크 정보
    net_io = psutil.net_io_counters()
    
    return jsonify({
        "cpu": {
            "percent": round(cpu_percent, 2),
            "count": cpu_count
        },
        "memory": {
            "percent": round(memory.percent, 2),
            "total_gb": round(memory_total_gb, 2),
            "used_gb": round(memory_used_gb, 2),
            "available_gb": round(memory_available_gb, 2)
        },
        "disk": {
            "percent": round(disk.percent, 2),
            "total_gb": round(disk_total_gb, 2),
            "used_gb": round(disk_used_gb, 2),
            "free_gb": round(disk_free_gb, 2)
        },
        "network": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    })
