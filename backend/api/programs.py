"""프로그램 관리 API 엔드포인트."""

from flask import Blueprint, request, session, jsonify
from datetime import datetime
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# Blueprint 생성
programs_api = Blueprint('programs_api', __name__, url_prefix='/api/programs')

# 설정 및 유틸리티 임포트
from config import PROGRAMS_JSON, STATUS_JSON
from utils.data_manager import load_json, save_json
from utils.decorators import require_auth, require_admin
from utils.responses import success_response, error_response, created_response
from utils.process_manager import (
    get_process_status,
    start_program,
    stop_program,
    restart_program,
    get_process_stats
)
from utils.cache import get_cache
from utils.logger import log_program_event as log_event_json, get_program_logs, calculate_uptime
from utils.webhook import send_webhook_notification
from utils.database import (
    get_all_programs,
    get_program_by_id,
    add_program as db_add_program,
    update_program as db_update_program,
    delete_program as db_delete_program,
    update_program_pid,
    remove_program_pid,
    log_program_event as db_log_event
)
from utils.process_monitor import mark_intentional_stop
from utils.path_validator import validate_program_path, normalize_path, get_path_info


@programs_api.route("", methods=["GET", "POST"])
@require_auth
def programs():
    """프로그램 목록 조회 및 등록 API."""
    if request.method == "GET":
        # 캐시 확인
        cache = get_cache()
        cached_programs = cache.get("all_programs")
        if cached_programs is not None:
            logger.debug("프로그램 목록 캐시 히트")
            return jsonify({"programs": cached_programs})
        
        # SQLite에서 프로그램 목록 조회
        programs_list = get_all_programs()
        
        # 캐시에 저장 (5초)
        cache.set("all_programs", programs_list)
        logger.debug(f"프로그램 목록 캐시 저장: {len(programs_list)}개")
        
        return jsonify({"programs": programs_list})
    
    # POST - 프로그램 등록 (관리자만)
    if session.get("role") != "admin":
        return error_response("관리자 권한이 필요합니다", 403)
    
    data = request.get_json()
    
    # 필수 필드 확인
    if not data.get("name"):
        return error_response("프로그램 이름이 필요합니다", 400)
    
    if not data.get("path"):
        return error_response("프로그램 경로가 필요합니다", 400)
    
    # 경로 유효성 검증
    is_valid, error_msg = validate_program_path(data["path"])
    if not is_valid:
        return error_response(error_msg, 400)
    
    # 경로 정규화 (절대 경로로 변환)
    normalized_path = normalize_path(data["path"])
    
    # 웹훅 URL 처리 (단일 또는 다중)
    webhook_urls = data.get("webhook_urls", data.get("webhook_url", []))
    if isinstance(webhook_urls, str):
        webhook_urls = [webhook_urls] if webhook_urls else []
    elif not isinstance(webhook_urls, list):
        webhook_urls = []
    
    # SQLite에 프로그램 추가
    program_id = db_add_program(
        name=data["name"],
        path=normalized_path,
        args=data.get("args", ""),
        webhook_urls=webhook_urls
    )
    
    logger.info(f"프로그램 등록: {data['name']} -> {normalized_path} (ID: {program_id})")
    
    # 캐시 무효화
    cache = get_cache()
    cache.delete("all_programs")
    logger.debug("프로그램 목록 캐시 무효화")
    
    return created_response(
        data={"id": program_id, "name": data["name"], "path": normalized_path},
        message="프로그램이 등록되었습니다",
        resource_id=program_id
    )


@programs_api.route("/<int:program_id>/start", methods=["POST"])
@require_auth
@require_admin
def start(program_id):
    """프로그램 실행 API (관리자만)."""
    program = get_program_by_id(program_id)
    if not program:
        return error_response("프로그램을 찾을 수 없습니다", 404)
    
    success, message, pid = start_program(program["path"], program.get("args", ""))
    
    # PID 저장
    if success and pid:
        update_program_pid(program_id, pid)
        print(f"💾 [Programs API] PID 저장: {program['name']} -> {pid}")
    
    # 로그 기록 및 웹훅 알림
    if success:
        db_log_event(program_id, "start", f"사용자: {session.get('user')}, PID: {pid}")
        webhook_urls = program.get("webhook_urls")
        send_webhook_notification(program["name"], "start", f"사용자: {session.get('user')}, PID: {pid}", "success", webhook_urls)
    
    return jsonify({"success": success, "message": message, "pid": pid})


@programs_api.route("/<int:program_id>/stop", methods=["POST"])
def stop(program_id):
    """프로그램 종료 API (관리자만)."""
    try:
        if "user" not in session or session.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        
        program = get_program_by_id(program_id)
        if not program:
            return jsonify({"error": "Program not found"}), 404
        
        # 강제 종료 옵션 확인 (쿼리 파라미터 또는 JSON 바디)
        force = request.args.get('force', 'false').lower() == 'true'
        if request.is_json:
            try:
                data = request.get_json()
                force = data.get('force', force)
            except:
                pass  # JSON 파싱 실패 시 쿼리 파라미터 사용
        
        # 의도적 종료 표시 (프로세스 모니터가 crash로 감지하지 않도록)
        mark_intentional_stop(program["name"])
        
        success, message = stop_program(program["path"], force=force)
        
        # PID 제거
        if success:
            remove_program_pid(program_id)
            print(f"🗑️ [Programs API] PID 제거: {program['name']}")
        
        # 로그 기록 및 웹훅 알림
        if success:
            stop_type = "강제 종료" if force else "종료"
            db_log_event(program_id, "stop", f"사용자: {session.get('user')}, 타입: {stop_type}")
            webhook_urls = program.get("webhook_urls")
            send_webhook_notification(program["name"], "stop", f"사용자: {session.get('user')}, 타입: {stop_type}", "warning", webhook_urls)
        
        return jsonify({"success": success, "message": message})
    except Exception as e:
        print(f"💥 [Programs API] stop API 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500


@programs_api.route("/<int:program_id>/restart", methods=["POST"])
def restart(program_id):
    """프로그램 재시작 API (게스트도 가능)."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    program = get_program_by_id(program_id)
    if not program:
        return jsonify({"error": "Program not found"}), 404
    
    success, message, pid = restart_program(program["path"], program.get("args", ""))
    
    # PID 업데이트
    if success and pid:
        update_program_pid(program_id, pid)
        print(f"🔄 [Programs API] PID 업데이트: {program['name']} -> {pid}")
    
    # 로그 기록 및 웹훅 알림
    if success:
        db_log_event(program_id, "restart", f"사용자: {session.get('user')}, PID: {pid}")
        webhook_urls = program.get("webhook_urls")
        send_webhook_notification(program["name"], "restart", f"사용자: {session.get('user')}, PID: {pid}", "info", webhook_urls)
    
    return jsonify({"success": success, "message": message, "pid": pid})


@programs_api.route("/<int:program_id>", methods=["PUT"])
def update(program_id):
    """프로그램 정보 수정 API (관리자만)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    program = get_program_by_id(program_id)
    if not program:
        return jsonify({"error": "Program not found"}), 404
    
    data = request.get_json()
    
    # 필수 필드 검증
    if not data.get("name"):
        return jsonify({"error": "프로그램 이름이 필요합니다."}), 400
    
    if not data.get("path"):
        return jsonify({"error": "프로그램 경로가 필요합니다."}), 400
    
    # 경로 유효성 검증
    is_valid, error_msg = validate_program_path(data["path"])
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    # 경로 정규화
    normalized_path = normalize_path(data["path"])
    
    # 웹훅 URL 처리
    webhook_urls = data.get("webhook_urls", data.get("webhook_url", []))
    if isinstance(webhook_urls, str):
        webhook_urls = [webhook_urls] if webhook_urls else []
    elif not isinstance(webhook_urls, list):
        webhook_urls = []
    
    # SQLite에서 프로그램 업데이트
    db_update_program(
        program_id=program_id,
        name=data["name"],
        path=normalized_path,
        args=data.get("args", ""),
        webhook_urls=webhook_urls
    )
    
    print(f"✅ [Programs API] 프로그램 수정: {data['name']} -> {normalized_path}")
    
    return jsonify({"success": True, "message": "프로그램 정보가 수정되었습니다."})


@programs_api.route("/<int:program_id>/delete", methods=["DELETE"])
def delete(program_id):
    """프로그램 삭제 API (관리자만)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    program = get_program_by_id(program_id)
    if not program:
        return jsonify({"error": "Program not found"}), 404
    
    db_delete_program(program_id)
    
    print(f"🗑️ [Programs API] 프로그램 삭제: {program['name']}")
    
    return jsonify({"success": True})


@programs_api.route("/status", methods=["GET"])
def status():
    """모든 프로그램의 실시간 상태 조회 (CPU/메모리 사용량 및 가동 시간 포함)."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    programs = get_all_programs()
    status_list = []
    
    for program in programs:
        # 저장된 PID 가져오기
        saved_pid = program.get("pid")
        
        # 프로세스 상태 및 리소스 사용량 조회 (PID 우선)
        stats = get_process_stats(program["path"], pid=saved_pid)
        
        # PID가 변경되었으면 업데이트
        if stats['running'] and stats['pid'] != saved_pid:
            update_program_pid(program['id'], stats['pid'])
            print(f"🔄 [Status] PID 업데이트: {program['name']} -> {stats['pid']}")
        
        # PID가 없어졌으면 제거
        if not stats['running'] and saved_pid:
            remove_program_pid(program['id'])
            print(f"🗑️ [Status] PID 제거: {program['name']}")
        
        # 가동 시간 계산
        uptime_info = calculate_uptime(program["name"])
        
        status_list.append({
            "id": program['id'],
            "name": program["name"],
            "running": stats['running'],
            "status": "실행 중" if stats['running'] else "중지됨",
            "cpu_percent": stats['cpu_percent'],
            "memory_mb": stats['memory_mb'],
            "memory_percent": stats['memory_percent'],
            "uptime": uptime_info['uptime_formatted'],
            "pid": stats['pid']
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


@programs_api.route("/validate-path", methods=["POST"])
def validate_path():
    """경로 유효성 검증 API (프런트엔드용)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json()
    path = data.get("path", "").strip()
    
    if not path:
        return jsonify({"valid": False, "error": "경로가 제공되지 않았습니다."}), 400
    
    # 경로 유효성 검증
    is_valid, error_msg = validate_program_path(path)
    
    if is_valid:
        # 경로 정보 조회
        path_info = get_path_info(path)
        normalized = normalize_path(path)
        
        return jsonify({
            "valid": True,
            "path": normalized,
            "info": path_info
        })
    else:
        return jsonify({
            "valid": False,
            "error": error_msg
        })
