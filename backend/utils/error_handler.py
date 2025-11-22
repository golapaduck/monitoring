"""전역 에러 처리 및 복구 시스템."""

import logging
import traceback
from flask import jsonify
from functools import wraps

# 로거 설정
logger = logging.getLogger(__name__)


class MonitoringError(Exception):
    """모니터링 시스템 기본 예외."""
    
    def __init__(self, message, error_code="INTERNAL_ERROR", status_code=500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class ProcessError(MonitoringError):
    """프로세스 관련 에러."""
    
    def __init__(self, message):
        super().__init__(message, "PROCESS_ERROR", 500)


class DatabaseError(MonitoringError):
    """데이터베이스 관련 에러."""
    
    def __init__(self, message):
        super().__init__(message, "DATABASE_ERROR", 500)


class ValidationError(MonitoringError):
    """입력값 검증 에러."""
    
    def __init__(self, message):
        super().__init__(message, "VALIDATION_ERROR", 400)


class AuthenticationError(MonitoringError):
    """인증 관련 에러."""
    
    def __init__(self, message):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class PermissionError(MonitoringError):
    """권한 관련 에러."""
    
    def __init__(self, message):
        super().__init__(message, "PERMISSION_ERROR", 403)


def handle_error(f):
    """에러 처리 데코레이터.
    
    모든 예외를 캐치하고 적절한 응답을 반환합니다.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except MonitoringError as e:
            logger.error(f"❌ {e.error_code}: {e.message}")
            return jsonify({
                "success": False,
                "error": e.message,
                "error_code": e.error_code
            }), e.status_code
        except Exception as e:
            logger.error(f"❌ 예상치 못한 에러: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "success": False,
                "error": "서버 내부 오류가 발생했습니다",
                "error_code": "INTERNAL_ERROR"
            }), 500
    
    return decorated_function


def register_error_handlers(app):
    """Flask 앱에 전역 에러 핸들러 등록.
    
    Args:
        app: Flask 애플리케이션
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """400 Bad Request 처리."""
        logger.warning(f"⚠️ 잘못된 요청: {error}")
        return jsonify({
            "success": False,
            "error": "잘못된 요청입니다",
            "error_code": "BAD_REQUEST"
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """401 Unauthorized 처리."""
        logger.warning(f"⚠️ 인증 실패: {error}")
        return jsonify({
            "success": False,
            "error": "인증이 필요합니다",
            "error_code": "UNAUTHORIZED"
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """403 Forbidden 처리."""
        logger.warning(f"⚠️ 권한 거부: {error}")
        return jsonify({
            "success": False,
            "error": "권한이 없습니다",
            "error_code": "FORBIDDEN"
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """404 Not Found 처리."""
        logger.warning(f"⚠️ 리소스를 찾을 수 없음: {error}")
        return jsonify({
            "success": False,
            "error": "요청한 리소스를 찾을 수 없습니다",
            "error_code": "NOT_FOUND"
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 Internal Server Error 처리."""
        logger.error(f"❌ 서버 내부 오류: {error}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": "서버 내부 오류가 발생했습니다",
            "error_code": "INTERNAL_ERROR"
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """예상치 못한 예외 처리."""
        logger.error(f"❌ 예상치 못한 에러: {str(error)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": "서버 내부 오류가 발생했습니다",
            "error_code": "INTERNAL_ERROR"
        }), 500


def log_error(level=logging.ERROR):
    """에러 로깅 데코레이터.
    
    Args:
        level: 로깅 레벨 (logging.ERROR, logging.WARNING 등)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.log(level, f"❌ {f.__name__} 실패: {str(e)}")
                logger.log(level, traceback.format_exc())
                raise
        
        return decorated_function
    
    return decorator
