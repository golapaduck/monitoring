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
    """시스템 리소스 상태 조회 (CPU, 메모리, 디스크 등) - 향후 구현."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    # TODO: psutil을 사용해서 시스템 리소스 정보 수집
    return jsonify({
        "cpu_percent": 0,
        "memory_percent": 0,
        "disk_percent": 0,
        "message": "Not implemented yet"
    })
