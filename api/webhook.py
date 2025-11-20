"""웹훅 설정 API 엔드포인트."""

from flask import Blueprint, request, session, jsonify

# Blueprint 생성
webhook_api = Blueprint('webhook_api', __name__, url_prefix='/api/webhook')

# 유틸리티 임포트
from utils.webhook import get_webhook_config, save_webhook_config, test_webhook


@webhook_api.route("/config", methods=["GET", "POST"])
def config():
    """웹훅 설정 조회 및 저장 API (관리자만)."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == "GET":
        # 웹훅 설정 조회
        config_data = get_webhook_config()
        return jsonify(config_data)
    
    # POST - 웹훅 설정 저장 (관리자만)
    if session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json()
    
    # 설정 유효성 검사
    if "url" in data and data["url"] and not data["url"].startswith(("http://", "https://")):
        return jsonify({"error": "Invalid URL format"}), 400
    
    save_webhook_config(data)
    
    return jsonify({"success": True, "message": "웹훅 설정이 저장되었습니다."})


@webhook_api.route("/test", methods=["POST"])
def test():
    """웹훅 테스트 API (관리자만)."""
    if "user" not in session or session.get("role") != "admin":
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json()
    url = data.get("url")
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "Invalid URL format"}), 400
    
    success, message = test_webhook(url)
    
    return jsonify({
        "success": success,
        "message": message
    })
