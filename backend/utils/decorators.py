"""API 엔드포인트용 데코레이터.

인증, 권한 체크 등의 공통 기능을 제공합니다.
"""

from functools import wraps
from flask import session, jsonify
from typing import Callable, Any


def require_auth(f: Callable) -> Callable:
    """인증 필수 데코레이터.
    
    세션에 사용자 정보가 없으면 401 Unauthorized 반환.
    
    Usage:
        @require_auth
        def my_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f: Callable) -> Callable:
    """관리자 권한 필수 데코레이터.
    
    세션의 role이 admin이 아니면 403 Forbidden 반환.
    require_auth와 함께 사용해야 합니다.
    
    Usage:
        @require_auth
        @require_admin
        def admin_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if session.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated_function


def require_role(role: str) -> Callable:
    """특정 역할 필수 데코레이터.
    
    Args:
        role: 필요한 역할 (예: 'admin', 'user')
    
    Usage:
        @require_auth
        @require_role('admin')
        def endpoint():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if session.get("role") != role:
                return jsonify({
                    "error": f"Forbidden: {role} role required"
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
