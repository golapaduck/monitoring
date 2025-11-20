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
from utils.logger import log_program_event, get_program_logs, calculate_uptime
from utils.webhook import send_webhook_notification


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
    
    # 로그 기록 및 웹훅 알림
    if success:
        log_program_event(program["name"], "start", f"사용자: {session.get('user')}")
        webhook_url = program.get("webhook_url")  # 프로그램별 웹훅 URL
        send_webhook_notification(program["name"], "start", f"사용자: {session.get('user')}", "success", webhook_url)
    
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
    
    # 로그 기록 및 웹훅 알림
    if success:
        log_program_event(program["name"], "stop", f"사용자: {session.get('user')}")
        webhook_url = program.get("webhook_url")  # 프로그램별 웹훅 URL
        send_webhook_notification(program["name"], "stop", f"사용자: {session.get('user')}", "warning", webhook_url)
    
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
    
    # 로그 기록 및 웹훅 알림
    if success:
        log_program_event(program["name"], "restart", f"사용자: {session.get('user')}")
        webhook_url = program.get("webhook_url")  # 프로그램별 웹훅 URL
        send_webhook_notification(program["name"], "restart", f"사용자: {session.get('user')}", "info", webhook_url)
    
    return jsonify({"success": success, "message": message})


@programs_api.route("/<int:program_id>", methods=["PUT"])
def update(program_id):
    """프로그램 정보 수정 API (관리자만)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    if program_id >= len(programs_data["programs"]):
        return jsonify({"error": "Program not found"}), 404
    
    data = request.get_json()
    
    # 필수 필드 검증
    if not data.get("name") or not data.get("path"):
        return jsonify({"error": "Name and path are required"}), 400
    
    # 프로그램 정보 업데이트
    programs_data["programs"][program_id] = {
        "name": data["name"],
        "path": data["path"],
        "args": data.get("args", ""),
        "webhook_url": data.get("webhook_url", "")
    }
    
    save_json(PROGRAMS_JSON, programs_data)
    
    return jsonify({"success": True, "message": "프로그램 정보가 수정되었습니다."})


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
    """모든 프로그램의 실시간 상태 조회 (CPU/메모리 사용량 및 가동 시간 포함)."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    status_list = []
    
    for idx, program in enumerate(programs_data["programs"]):
        # 프로세스 상태 및 리소스 사용량 조회
        stats = get_process_stats(program["path"])
        
        # 가동 시간 계산
        uptime_info = calculate_uptime(program["name"])
        
        status_list.append({
            "id": idx,
            "name": program["name"],
            "running": stats['running'],
            "status": "실행 중" if stats['running'] else "중지됨",
            "cpu_percent": stats['cpu_percent'],
            "memory_mb": stats['memory_mb'],
            "memory_percent": stats['memory_percent'],
            "uptime": uptime_info['uptime_formatted']
        })
    
    # 상태 데이터를 JSON 파일에도 저장
    status_data = {
        "last_update": datetime.now().isoformat(),
        "programs_status": status_list
    }
    save_json(STATUS_JSON, status_data)
    
    return jsonify(status_data)


@programs_api.route("/<int:program_id>/logs", methods=["GET"])
def logs(program_id):
    """프로그램 로그 조회 API."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    if program_id >= len(programs_data["programs"]):
        return jsonify({"error": "Program not found"}), 404
    
    program = programs_data["programs"][program_id]
    limit = request.args.get('limit', 50, type=int)
    
    logs = get_program_logs(program["name"], limit=limit)
    
    return jsonify({
        "program_name": program["name"],
        "logs": logs,
        "total": len(logs)
    })
