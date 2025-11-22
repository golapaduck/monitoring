"""헬스 체크 및 시스템 상태 API."""

from flask import Blueprint, jsonify
import psutil
import logging
from pathlib import Path
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)

# Blueprint 생성
health_api = Blueprint('health_api', __name__, url_prefix='/api/health')


@health_api.route('/status', methods=['GET'])
def health_status():
    """헬스 체크 상태 조회.
    
    Returns:
        JSON: {
            "status": "healthy" | "degraded" | "unhealthy",
            "timestamp": ISO 8601 시간,
            "checks": {
                "database": {"status": "ok", "message": "..."},
                "memory": {"status": "ok", "usage_percent": 45.2},
                "disk": {"status": "ok", "usage_percent": 62.1},
                "processes": {"status": "ok", "count": 5},
                "config": {"status": "ok", "message": "..."}
            },
            "uptime_seconds": 3600
        }
    """
    try:
        checks = {}
        overall_status = "healthy"
        
        # 1. 데이터베이스 확인
        checks["database"] = _check_database()
        if checks["database"]["status"] != "ok":
            overall_status = "degraded"
        
        # 2. 메모리 확인
        checks["memory"] = _check_memory()
        if checks["memory"]["status"] != "ok":
            overall_status = "degraded"
        
        # 3. 디스크 확인
        checks["disk"] = _check_disk()
        if checks["disk"]["status"] != "ok":
            overall_status = "degraded"
        
        # 4. 프로세스 확인
        checks["processes"] = _check_processes()
        if checks["processes"]["status"] != "ok":
            overall_status = "degraded"
        
        # 5. 설정 확인
        checks["config"] = _check_config()
        if checks["config"]["status"] != "ok":
            overall_status = "degraded"
        
        # 시스템 가동 시간
        import time
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)
        
        return jsonify({
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "uptime_seconds": uptime_seconds
        }), 200
        
    except Exception as e:
        logger.error(f"❌ 헬스 체크 실패: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500


def _check_database():
    """데이터베이스 상태 확인."""
    try:
        from utils.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        return {
            "status": "ok",
            "message": "데이터베이스 연결 정상"
        }
    except Exception as e:
        logger.error(f"❌ 데이터베이스 확인 실패: {str(e)}")
        return {
            "status": "error",
            "message": f"데이터베이스 연결 실패: {str(e)}"
        }


def _check_memory():
    """메모리 상태 확인."""
    try:
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        
        status = "ok"
        if usage_percent > 90:
            status = "critical"
        elif usage_percent > 75:
            status = "warning"
        
        return {
            "status": status,
            "usage_percent": round(usage_percent, 2),
            "used_mb": round(memory.used / (1024 * 1024), 2),
            "total_mb": round(memory.total / (1024 * 1024), 2)
        }
    except Exception as e:
        logger.error(f"❌ 메모리 확인 실패: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def _check_disk():
    """디스크 상태 확인."""
    try:
        disk = psutil.disk_usage('C:\\')
        usage_percent = disk.percent
        
        status = "ok"
        if usage_percent > 95:
            status = "critical"
        elif usage_percent > 85:
            status = "warning"
        
        return {
            "status": status,
            "usage_percent": round(usage_percent, 2),
            "used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
            "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            "free_gb": round(disk.free / (1024 * 1024 * 1024), 2)
        }
    except Exception as e:
        logger.error(f"❌ 디스크 확인 실패: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def _check_processes():
    """프로세스 상태 확인."""
    try:
        from utils.database import get_all_programs
        
        programs = get_all_programs()
        running_count = sum(1 for p in programs if p.get("pid"))
        
        return {
            "status": "ok",
            "total": len(programs),
            "running": running_count,
            "stopped": len(programs) - running_count
        }
    except Exception as e:
        logger.error(f"❌ 프로세스 확인 실패: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def _check_config():
    """설정 상태 확인."""
    try:
        from config import Config
        
        issues = []
        
        # SECRET_KEY 확인
        if Config.SECRET_KEY == "dev-monitoring-secret-key":
            issues.append("기본 SECRET_KEY 사용 중 (프로덕션에서는 변경 필수)")
        
        # FLASK_DEBUG 확인
        if Config.FLASK_DEBUG and Config.IS_PRODUCTION:
            issues.append("프로덕션 환경에서 DEBUG 모드 활성화")
        
        status = "warning" if issues else "ok"
        
        return {
            "status": status,
            "environment": "production" if Config.IS_PRODUCTION else "development",
            "issues": issues if issues else []
        }
    except Exception as e:
        logger.error(f"❌ 설정 확인 실패: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@health_api.route('/ready', methods=['GET'])
def readiness_check():
    """준비 상태 확인 (Kubernetes 호환).
    
    Returns:
        JSON: {"ready": true/false}
    """
    try:
        # 데이터베이스 연결 확인
        from utils.database import get_connection
        conn = get_connection()
        conn.close()
        
        return jsonify({"ready": True}), 200
    except Exception as e:
        logger.error(f"❌ 준비 상태 확인 실패: {str(e)}")
        return jsonify({"ready": False, "error": str(e)}), 503


@health_api.route('/live', methods=['GET'])
def liveness_check():
    """생존 상태 확인 (Kubernetes 호환).
    
    Returns:
        JSON: {"alive": true/false}
    """
    try:
        return jsonify({"alive": True}), 200
    except Exception as e:
        logger.error(f"❌ 생존 상태 확인 실패: {str(e)}")
        return jsonify({"alive": False, "error": str(e)}), 503
