"""웹 페이지 라우트 (로그인, 대시보드 등)."""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from pathlib import Path
import json
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# Blueprint 생성
web_bp = Blueprint('web', __name__)

# 설정 및 유틸리티 임포트
from config import USERS_JSON, PROGRAMS_JSON, STATUS_JSON
from utils.data_manager import load_json
from utils.auth import verify_password
from utils.database import get_user_by_username
from utils.login_security import get_login_security_manager, prevent_session_fixation


@web_bp.route("/")
def index():
    """메인 페이지 - 로그인 여부에 따라 리다이렉트."""
    if "user" in session:
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    """로그인 페이지 및 처리.
    
    보안 기능:
    - bcrypt 기반 비밀번호 검증
    - 로그인 시도 횟수 제한 (5회)
    - 계정 잠금 (15분)
    - 세션 고정 공격 방지 (로그인 후 세션 재생성)
    - 일반적인 오류 메시지 (사용자명 존재 여부 미노출)
    - Rate limiting 적용 (Flask-Limiter)
    """
    error = None
    security_manager = get_login_security_manager()
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # 입력값 검증
        if not username or not password:
            error = "아이디와 비밀번호를 입력해주세요."
            logger.warning("로그인 실패: 입력값 누락")
        else:
            # 🔒 계정 잠금 확인
            is_locked, remaining_time = security_manager.is_account_locked(username)
            if is_locked:
                minutes = remaining_time // 60
                seconds = remaining_time % 60
                error = f"계정이 잠겼습니다. {minutes}분 {seconds}초 후에 다시 시도해주세요."
                logger.warning(f"❌ 로그인 차단: {username} (계정 잠금, 남은 시간: {remaining_time}초)")
                
                if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                    return jsonify({
                        "success": False, 
                        "error": error,
                        "locked": True,
                        "remaining_time": remaining_time
                    }), 429
            else:
                # SQLite에서 사용자 조회
                user = get_user_by_username(username)
                
                # 사용자가 존재하고 비밀번호가 일치하는지 확인
                if user and verify_password(password, user["password"]):
                    # 🔒 로그인 성공 기록
                    security_manager.record_login_attempt(username, success=True)
                    
                    # 🔒 세션 고정 공격 방지: 세션 ID 재생성
                    prevent_session_fixation(session)
                    
                    # 세션을 영구적으로 설정 (타임아웃 적용)
                    session.permanent = True
                    session["user"] = username
                    session["role"] = user["role"]
                    session["login_time"] = __import__('time').time()  # 로그인 시간 기록
                    
                    logger.info(f"✅ 사용자 '{username}' 로그인 성공 (역할: {user['role']})")
                    
                    # React 프론트엔드에서 요청한 경우 JSON 응답
                    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                        return jsonify({"success": True, "user": {"username": username, "role": user["role"]}}), 200
                    
                    return redirect(url_for("web.dashboard"))
                else:
                    # 🔒 로그인 실패 기록
                    security_manager.record_login_attempt(username, success=False)
                    
                    # 🔒 계정 잠금 확인
                    is_locked, failure_count = security_manager.check_and_lock_if_needed(username)
                    
                    if is_locked:
                        error = "로그인 시도 횟수를 초과했습니다. 계정이 15분간 잠겼습니다."
                        logger.warning(f"❌ 계정 잠금: {username} (실패 횟수: {failure_count})")
                    else:
                        remaining = security_manager.get_remaining_attempts(username)
                        # 🔒 정보 누출 방지: 일반적인 오류 메시지
                        error = f"아이디 또는 비밀번호가 올바르지 않습니다. (남은 시도: {remaining}회)"
                        logger.warning(f"❌ 로그인 실패: {username} (남은 시도: {remaining}회)")
                    
                    # React 프론트엔드에서 요청한 경우 JSON 응답
                    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                        return jsonify({
                            "success": False, 
                            "error": error,
                            "locked": is_locked,
                            "remaining_attempts": security_manager.get_remaining_attempts(username)
                        }), 401
    
    return render_template("login.html", error=error)


@web_bp.route("/logout")
def logout():
    """로그아웃 처리."""
    session.clear()
    return redirect(url_for("web.login"))


@web_bp.route("/dashboard")
def dashboard():
    """대시보드 - 역할에 따라 다른 화면 표시."""
    if "user" not in session:
        return redirect(url_for("web.login"))
    
    role = session.get("role", "guest")
    programs_data = load_json(PROGRAMS_JSON, {"programs": []})
    status_data = load_json(STATUS_JSON, {"programs_status": []})
    
    return render_template(
        "dashboard.html",
        username=session["user"],
        role=role,
        programs=programs_data.get("programs", []),
        status=status_data.get("programs_status", [])
    )


@web_bp.route("/api/session")
def check_session():
    """세션 확인 API - 프론트엔드 인증 체크용."""
    from flask import jsonify
    
    if "user" not in session:
        return jsonify({
            "logged_in": False,
            "authenticated": False
        }), 401
    
    return jsonify({
        "logged_in": True,
        "authenticated": True,
        "username": session.get("user"),
        "role": session.get("role")
    }), 200


@web_bp.route("/health")
def health():
    """헬스체크 엔드포인트 - 외부 모니터링용."""
    from flask import jsonify
    import time
    
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "monitoring"
    }), 200
