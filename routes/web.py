"""웹 페이지 라우트 (로그인, 대시보드 등)."""

from flask import Blueprint, render_template, request, redirect, url_for, session
from pathlib import Path
import json

# Blueprint 생성
web_bp = Blueprint('web', __name__)

# 설정 및 유틸리티 임포트
from config import USERS_JSON, PROGRAMS_JSON, STATUS_JSON
from utils.data_manager import load_json


@web_bp.route("/")
def index():
    """메인 페이지 - 로그인 여부에 따라 리다이렉트."""
    if "user" in session:
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    """로그인 페이지 및 처리."""
    error = None
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        users_data = load_json(USERS_JSON, {"users": []})
        user = next(
            (u for u in users_data.get("users", []) 
             if u["username"] == username and u["password"] == password),
            None
        )
        
        if user:
            session["user"] = username
            session["role"] = user["role"]
            return redirect(url_for("web.dashboard"))
        else:
            error = "아이디 또는 비밀번호가 올바르지 않습니다."
    
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
