"""웹 페이지 라우트 (API 전용, React 프론트엔드 사용)."""

from flask import Blueprint, request, redirect, url_for, session, jsonify
from pathlib import Path
import json
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# Blueprint 생성
web_bp = Blueprint('web', __name__)

# 설정 및 유틸리티 임포트
from utils.auth import verify_password
from utils.database import get_user_by_username
from utils.login_security import get_login_security_manager, prevent_session_fixation


@web_bp.route("/")
def index():
    """메인 페이지 - React 프론트엔드로 리다이렉트."""
    # React 프론트엔드가 라우팅 처리
    return redirect("/")


@web_bp.route("/api/login", methods=["POST"])
def login():
    """로그인 API (JSON 전용).
    
    보안 기능:
    - bcrypt 기반 비밀번호 검증
    - 로그인 시도 횟수 제한 (5회)
    - 계정 잠금 (15분)
    - 세션 고정 공격 방지 (로그인 후 세션 재생성)
    - 일반적인 오류 메시지 (사용자명 존재 여부 미노출)
    - Rate limiting 적용 (Flask-Limiter)
    """
    security_manager = get_login_security_manager()
    
    # JSON 데이터 파싱
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "잘못된 요청입니다"}), 400
    
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    # 입력값 검증
    if not username or not password:
        logger.warning("로그인 실패: 입력값 누락")
        return jsonify({"success": False, "error": "아이디와 비밀번호를 입력해주세요"}), 400
    
    # 🔒 계정 잠금 확인
    is_locked, remaining_time = security_manager.is_account_locked(username)
    if is_locked:
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        error = f"계정이 잠겼습니다. {minutes}분 {seconds}초 후에 다시 시도해주세요."
        logger.warning(f"❌ 로그인 차단: {username} (계정 잠금, 남은 시간: {remaining_time}초)")
        return jsonify({
            "success": False, 
            "error": error,
            "locked": True,
            "remaining_time": remaining_time
        }), 429
    
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
        
        return jsonify({"success": True, "user": {"username": username, "role": user["role"]}}), 200
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
            error = f"아이디 또는 비밀밀번호가 올바르지 않습니다. (남은 시도: {remaining}회)"
            logger.warning(f"❌ 로그인 실패: {username} (남은 시도: {remaining}회)")
        
        return jsonify({
            "success": False, 
            "error": error,
            "locked": is_locked,
            "remaining_attempts": security_manager.get_remaining_attempts(username)
        }), 401


@web_bp.route("/api/logout", methods=["POST"])
def logout():
    """로그아웃 API."""
    session.clear()
    return jsonify({"success": True, "message": "로그아웃되었습니다"}), 200


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
