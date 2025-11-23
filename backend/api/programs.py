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
from utils.rate_limiter import limiter, get_rate_limit
from utils.database import (
    get_all_programs,
    get_program_by_id,
    add_program as db_add_program,
    update_program as db_update_program,
    delete_program as db_delete_program,
    update_program_pid,
    remove_program_pid,
    set_graceful_shutdown,
    clear_graceful_shutdown,
    log_program_event as db_log_event
)
from utils.process_monitor import mark_intentional_stop, request_immediate_check
from utils.path_validator import validate_program_path, normalize_path, get_path_info
from plugins.loader import get_plugin_loader


@programs_api.route("", methods=["GET", "POST"])
@require_auth
@limiter.limit(get_rate_limit("programs_list"))
def programs():
    """프로그램 목록 조회 및 등록 API."""
    if request.method == "GET":
        # 캐시 확인 (10초 TTL)
        cache = get_cache()
        cached_programs = cache.get("all_programs")
        if cached_programs is not None:
            logger.debug("프로그램 목록 캐시 히트")
            return jsonify({"programs": cached_programs})
        
        # SQLite에서 프로그램 목록 조회 (최적화된 쿼리)
        programs_list = get_all_programs()
        
        # 캐시에 저장 (10초, 태그 추가)
        cache.set("all_programs", programs_list, tags=["programs", "programs:list"])
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
    
    # 캐시 무효화 (태그 기반)
    cache = get_cache()
    invalidated = cache.invalidate_by_tag("programs")
    logger.info(f"프로그램 등록 - 캐시 무효화: {invalidated}개")
    
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
        
        # 캐시 무효화 (즉시 상태 반영)
        cache = get_cache()
        cache.delete("programs_status")
        print(f"🗑️ [Programs API] 캐시 무효화: programs_status")
        
        # 즉시 상태 확인 요청 (빠른 감지)
        request_immediate_check()
    
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
        
        success = False
        message = ""
        shutdown_method = "일반 종료"
        
        # 펠월드 플러그인이 있고 강제 종료가 아니면 Graceful Shutdown 시도
        loader = get_plugin_loader()
        palworld_plugin = loader.get_plugin_instance(program_id, "palworld")
        
        if palworld_plugin and not force:
            # 펠월드 API를 사용하여 Graceful Shutdown
            shutdown_wait_time = 30
            print(f"🎮 [Programs API] 펠월드 Graceful Shutdown 시작: {program['name']} (대기: {shutdown_wait_time}초)")
            
            result = palworld_plugin.execute_action("shutdown_server", {
                "waittime": str(shutdown_wait_time),
                "message": "관리자가 서버를 종료합니다"
            })
            
            if result.get("success"):
                success = True
                message = f"펠월드 API를 사용하여 서버를 종료했습니다 (약 {shutdown_wait_time}초 소요)"
                shutdown_method = "Graceful Shutdown"
                
                # Graceful Shutdown 상태 저장
                set_graceful_shutdown(program_id, shutdown_wait_time)
                print(f"✅ [Programs API] 펠월드 Graceful Shutdown 성공: {program['name']}")
            else:
                # API 실패 시 일반 종료로 폴백
                print(f"⚠️ [Programs API] 펠월드 API 실패, 일반 종료로 폴백: {result.get('message')}")
                success, message = stop_program(program["path"], force=False)
                shutdown_method = "일반 종료 (폴백)"
        else:
            # 일반 종료 또는 강제 종료
            success, message = stop_program(program["path"], force=force)
            shutdown_method = "강제 종료" if force else "일반 종료"
        
        # PID 제거 (Graceful Shutdown이 아닌 경우만)
        if success and shutdown_method != "Graceful Shutdown":
            remove_program_pid(program_id)
            print(f"🗑️ [Programs API] PID 제거: {program['name']} (방법: {shutdown_method})")
        
        # 로그 기록 및 웹훅 알림
        if success:
            stop_type = "강제 종료" if force else "종료"
            db_log_event(program_id, "stop", f"사용자: {session.get('user')}, 타입: {stop_type}")
            webhook_urls = program.get("webhook_urls")
            send_webhook_notification(program["name"], "stop", f"사용자: {session.get('user')}, 타입: {stop_type}", "warning", webhook_urls)
            
            # 캐시 무효화 (즉시 상태 반영)
            cache = get_cache()
            cache.delete("programs_status")
            print(f"🗑️ [Programs API] 캐시 무효화: programs_status")
            
            # 즉시 상태 확인 요청 (빠른 감지)
            request_immediate_check()
        
        return jsonify({
            "success": success,
            "message": message,
            "shutdown_method": shutdown_method
        })
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


@programs_api.route("/<int:program_id>", methods=["GET"])
@require_auth
def get_program(program_id):
    """프로그램 상세 조회 API (캐싱 적용)."""
    # 캐시 확인 (30초 TTL)
    cache = get_cache()
    cache_key = f"program:{program_id}"
    cached_program = cache.get(cache_key)
    if cached_program is not None:
        logger.debug(f"프로그램 캐시 히트: program_id={program_id}")
        return jsonify({"program": cached_program})
    
    # DB에서 조회
    program = get_program_by_id(program_id)
    if not program:
        return error_response("프로그램을 찾을 수 없습니다", 404)
    
    # 캐시에 저장 (30초, 태그 추가)
    cache.set(cache_key, program, tags=["programs", f"program:{program_id}"])
    logger.debug(f"프로그램 캐시 저장: program_id={program_id}")
    
    return jsonify({"program": program})


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
    
    # 캐시 무효화 (태그 기반)
    cache = get_cache()
    invalidated = cache.invalidate_multiple_tags(["programs", f"program:{program_id}"])
    logger.info(f"프로그램 수정 - 캐시 무효화: {invalidated}개")
    
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
    
    # 캐시 무효화 (태그 기반)
    cache = get_cache()
    invalidated = cache.invalidate_multiple_tags(["programs", f"program:{program_id}"])
    logger.info(f"프로그램 삭제 - 캐시 무효화: {invalidated}개")
    
    return jsonify({"success": True})


@programs_api.route("/status", methods=["GET"])
@limiter.exempt  # 폴링을 위해 Rate Limit 제외
def status():
    """모든 프로그램의 실시간 상태 조회 (캐싱 적용 - 2초 TTL)."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    programs = get_all_programs()
    
    # Graceful Shutdown 중인 프로그램이 있는지 확인
    has_shutting_down = any(
        program.get("shutdown_start") and program.get("shutdown_end")
        for program in programs
    )
    
    # Graceful Shutdown 중이면 캐시 사용 안 함 (실시간 카운트다운 필요)
    cache = get_cache()
    cache_key = "programs_status"
    
    if not has_shutting_down:
        cached_status = cache.get(cache_key)
        if cached_status is not None:
            print(f"📦 [Status API] 캐시 히트 - {len(cached_status.get('programs_status', []))}개 프로그램")
            return jsonify(cached_status)
    
    print("🔍 [Status API] 캐시 미스 - 새로 조회" + (" (Graceful Shutdown 진행 중)" if has_shutting_down else ""))
    
    status_list = []
    
    for program in programs:
        # 저장된 PID 가져오기
        saved_pid = program.get("pid")
        shutdown_start = program.get("shutdown_start")
        shutdown_end = program.get("shutdown_end")
        
        # 프로세스 상태 및 리소스 사용량 조회 (PID 우선)
        stats = get_process_stats(program["path"], pid=saved_pid)
        
        # Graceful Shutdown 상태 확인
        import time
        current_time = int(time.time())
        is_shutting_down = False
        shutdown_remaining = 0
        graceful_shutdown_completed = False
        
        if shutdown_start and shutdown_end:
            if current_time < shutdown_end:
                # 아직 종료 중
                is_shutting_down = True
                shutdown_remaining = shutdown_end - current_time
            else:
                # 종료 완료 - 상태 초기화
                clear_graceful_shutdown(program['id'])
                if saved_pid:
                    remove_program_pid(program['id'])
                    print(f"🗑️ [Status] Graceful Shutdown 완료 - PID 제거: {program['name']}")
                graceful_shutdown_completed = True
                # 프로세스가 종료되었으므로 stats['running']을 False로 강제 설정
                stats['running'] = False
        
        # PID가 변경되었으면 업데이트
        if stats['running'] and stats['pid'] != saved_pid and not is_shutting_down:
            update_program_pid(program['id'], stats['pid'])
            print(f"🔄 [Status] PID 업데이트: {program['name']} -> {stats['pid']}")
        
        # PID가 없어졌으면 제거 (Graceful Shutdown이 아닌 경우만)
        if not stats['running'] and saved_pid and not is_shutting_down:
            remove_program_pid(program['id'])
            print(f"🗑️ [Status] PID 제거: {program['name']}")
        
        # 가동 시간 계산
        uptime_info = calculate_uptime(program["name"])
        
        # 상태 결정
        if is_shutting_down:
            status = "shutting_down"
            status_text = f"종료 중 ({shutdown_remaining}초 남음)"
        elif stats['running']:
            status = "running"
            status_text = "실행 중"
        else:
            status = "stopped"
            status_text = "중지됨"
        
        status_list.append({
            "id": program['id'],
            "name": program["name"],
            "running": stats['running'],
            "status": status,
            "status_text": status_text,
            "cpu_percent": stats['cpu_percent'],
            "memory_mb": stats['memory_mb'],
            "memory_percent": stats['memory_percent'],
            "uptime": uptime_info['uptime_formatted'],
            "pid": stats['pid'],
            "shutdown_remaining": shutdown_remaining if is_shutting_down else None
        })
    
    # 상태 데이터를 JSON 파일에도 저장
    status_data = {
        "last_update": datetime.now().isoformat(),
        "programs_status": status_list
    }
    save_json(STATUS_JSON, status_data)
    
    # 캐시에 저장 (Graceful Shutdown 중이 아닐 때만)
    if not has_shutting_down:
        cache.set(cache_key, status_data)
        print(f"💾 [Status API] 캐시 저장 - {len(status_list)}개 프로그램")
    else:
        print(f"⏳ [Status API] 캐시 저장 안 함 (Graceful Shutdown 진행 중) - {len(status_list)}개 프로그램")
    
    print(f"📤 [Status API] 응답 데이터: {status_data}")
    
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
