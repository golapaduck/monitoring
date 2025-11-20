"""프로그램 관리 API 엔드포인트."""

from flask import Blueprint, request, session, jsonify
from datetime import datetime

# Blueprint 생성
programs_api = Blueprint('programs_api', __name__, url_prefix='/api/programs')

# 설정 및 유틸리티 임포트
from config import PROGRAMS_JSON, STATUS_JSON
from utils.data_manager import load_json, save_json
from utils.process_manager import (
    get_process_status,
    start_program,
    stop_program,
    restart_program,
    get_process_stats
)


@programs_api.route("", methods=["GET", "POST"])
def programs():
    """프로그램 목록 조회 및 등록 API."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == "GET":
        # 프로그램 목록 조회
        programs_data = load_json(PROGRAMS_JSON, {"programs": []})
        return jsonify(programs_data)
    
    # POST - 프로그램 등록 (관리자만)
    if session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json()
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    programs_data["programs"].append(data)
    save_json(PROGRAMS_JSON, programs_data)
    
    return jsonify({"success": True})


@programs_api.route("/<int:program_id>/start", methods=["POST"])
def start(program_id):
    """프로그램 실행 API (관리자만)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    if program_id >= len(programs_data["programs"]):
        return jsonify({"error": "Program not found"}), 404
    
    program = programs_data["programs"][program_id]
    success, message = start_program(program["path"], program.get("args", ""))
    
    return jsonify({"success": success, "message": message})


@programs_api.route("/<int:program_id>/stop", methods=["POST"])
def stop(program_id):
    """프로그램 종료 API (관리자만)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    if program_id >= len(programs_data["programs"]):
        return jsonify({"error": "Program not found"}), 404
    
    program = programs_data["programs"][program_id]
    success, message = stop_program(program["path"])
    
    return jsonify({"success": success, "message": message})


@programs_api.route("/<int:program_id>/restart", methods=["POST"])
def restart(program_id):
    """프로그램 재시작 API (게스트도 가능)."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    if program_id >= len(programs_data["programs"]):
        return jsonify({"error": "Program not found"}), 404
    
    program = programs_data["programs"][program_id]
    success, message = restart_program(program["path"], program.get("args", ""))
    
    return jsonify({"success": success, "message": message})


@programs_api.route("/<int:program_id>/delete", methods=["DELETE"])
def delete(program_id):
    """프로그램 삭제 API (관리자만)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    if program_id >= len(programs_data["programs"]):
        return jsonify({"error": "Program not found"}), 404
    
    del programs_data["programs"][program_id]
    save_json(PROGRAMS_JSON, programs_data)
    
    return jsonify({"success": True})


@programs_api.route("/status", methods=["GET"])
def status():
    """모든 프로그램의 실시간 상태 조회 (CPU/메모리 사용량 포함)."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    status_list = []
    
    for idx, program in enumerate(programs_data["programs"]):
        # 프로세스 상태 및 리소스 사용량 조회
        stats = get_process_stats(program["path"])
        
        status_list.append({
            "id": idx,
            "name": program["name"],
            "running": stats['running'],
            "status": "실행 중" if stats['running'] else "중지됨",
            "cpu_percent": stats['cpu_percent'],
            "memory_mb": stats['memory_mb'],
            "memory_percent": stats['memory_percent']
        })
    
    # 상태 데이터를 JSON 파일에도 저장
    status_data = {
        "last_update": datetime.now().isoformat(),
        "programs_status": status_list
    }
    save_json(STATUS_JSON, status_data)
    
    return jsonify(status_data)
