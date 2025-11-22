"""인증 및 세션 관리 API (React 프론트엔드용)."""

import time
import logging
from flask import Blueprint, request, session, jsonify

from utils.auth import verify_password
from utils.database import get_user_by_username
from utils.login_security import get_login_security_manager, prevent_session_fixation

# 로거 설정
logger = logging.getLogger(__name__)

# Blueprint 생성
web_bp = Blueprint('web', __name__)


# ===== 헬퍼 함수 =====

def _create_error_response(error: str, status_code: int = 400, **kwargs) -> tuple:
    """에러 응답 생성 헬퍼."""
    response = {"success": False, "error": error}
    response.update(kwargs)
    return jsonify(response), status_code


def _create_success_response(data: dict = None, message: str = None, status_code: int = 200) -> tuple:
    """성공 응답 생성 헬퍼."""
    response = {"success": True}
    if data:
        response.update(data)
    if message:
        response["message"] = message
    return jsonify(response), status_code


def _handle_account_locked(username: str, remaining_time: int) -> tuple:
    """계정 잠금 처리."""
    minutes = remaining_time // 60
    seconds = remaining_time % 60
    error = f"계정이 잠겼습니다. {minutes}분 {seconds}초 후에 다시 시도해주세요."
    logger.warning(f"로그인 차단: {username} (계정 잠금, 남은 시간: {remaining_time}초)")
    return _create_error_response(
        error, 
        status_code=429,
        locked=True,
        remaining_time=remaining_time
    )


def _handle_login_success(username: str, user: dict, security_manager) -> tuple:
    """로그인 성공 처리."""
    # 로그인 성공 기록
    security_manager.record_login_attempt(username, success=True)
    
    # 세션 고정 공격 방지
    prevent_session_fixation(session)
    
    # 세션 설정
    session.permanent = True
    session["user"] = username
    session["role"] = user["role"]
    session["login_time"] = time.time()
    
    logger.info(f"사용자 '{username}' 로그인 성공 (역할: {user['role']})")
    
    return _create_success_response(
        data={"user": {"username": username, "role": user["role"]}}
    )


def _handle_login_failure(username: str, security_manager) -> tuple:
    """로그인 실패 처리."""
    # 로그인 실패 기록
    security_manager.record_login_attempt(username, success=False)
    
    # 계정 잠금 확인
    is_locked, failure_count = security_manager.check_and_lock_if_needed(username)
    
    if is_locked:
        error = "로그인 시도 횟수를 초과했습니다. 계정이 15분간 잠겼습니다."
        logger.warning(f"계정 잠금: {username} (실패 횟수: {failure_count})")
    else:
        remaining = security_manager.get_remaining_attempts(username)
        error = f"아이디 또는 비밀번호가 올바르지 않습니다. (남은 시도: {remaining}회)"
        logger.warning(f"로그인 실패: {username} (남은 시도: {remaining}회)")
    
    return _create_error_response(
        error,
        status_code=401,
        locked=is_locked,
        remaining_attempts=security_manager.get_remaining_attempts(username)
    )


# ===== API 엔드포인트 =====


@web_bp.route("/login", methods=["GET", "POST"])
def login_page():
    """로그인 페이지 및 로그인 처리."""
    if request.method == "GET":
        # GET 요청: React 앱으로 리다이렉트
        from flask import redirect
        return redirect("/")
    else:
        # POST 요청: 로그인 처리 (login() 함수 호출)
        return login()


@web_bp.route("/api/login", methods=["POST"])
def login():
    """로그인 API.
    
    보안 기능:
    - bcrypt 기반 비밀번호 검증
    - 로그인 시도 횟수 제한 (5회)
    - 계정 잠금 (15분)
    - 세션 고정 공격 방지
    - 일반적인 오류 메시지 (정보 누출 방지)
    """
    # 디버깅: 요청 정보 출력
    print(f"[Login Debug] Content-Type: {request.content_type}")
    print(f"[Login Debug] Request data: {request.data}")
    print(f"[Login Debug] Request form: {request.form}")
    
    # JSON 데이터 파싱 (Content-Type 체크 안 함)
    data = request.get_json(force=True, silent=True)
    
    # JSON 파싱 실패 시 form 데이터 확인
    if not data:
        if request.form:
            data = request.form.to_dict()
            print(f"[Login Debug] Using form data: {data}")
        else:
            print(f"[Login Debug] No data found")
            return _create_error_response("잘못된 요청입니다")
    
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    # 입력값 검증
    if not username or not password:
        logger.warning("로그인 실패: 입력값 누락")
        return _create_error_response("아이디와 비밀번호를 입력해주세요")
    
    security_manager = get_login_security_manager()
    
    # 계정 잠금 확인
    is_locked, remaining_time = security_manager.is_account_locked(username)
    if is_locked:
        return _handle_account_locked(username, remaining_time)
    
    # 사용자 인증
    user = get_user_by_username(username)
    if user and verify_password(password, user["password"]):
        return _handle_login_success(username, user, security_manager)
    else:
        return _handle_login_failure(username, security_manager)


@web_bp.route("/logout", methods=["GET"])
def logout_page():
    """로그아웃 페이지 (GET 요청 처리)."""
    session.clear()
    from flask import redirect
    return redirect("/")


@web_bp.route("/api/logout", methods=["POST"])
def logout():
    """로그아웃 API (POST 요청 처리)."""
    session.clear()
    return _create_success_response(message="로그아웃되었습니다")


@web_bp.route("/api/session")
def check_session():
    """세션 확인 API - 프론트엔드 인증 체크용."""
    if "user" not in session:
        return _create_error_response(
            "인증되지 않음",
            status_code=401,
            logged_in=False,
            authenticated=False
        )
    
    return _create_success_response(
        data={
            "logged_in": True,
            "authenticated": True,
            "username": session.get("user"),
            "role": session.get("role")
        }
    )


@web_bp.route("/health")
def health():
    """헬스체크 엔드포인트 - 외부 모니터링용."""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "monitoring"
    }), 200
