"""헬스 체크 API 엔드포인트."""

from flask import Blueprint, jsonify
import psutil
import time
from datetime import datetime
from utils.decorators import require_auth, require_admin
from utils.responses import success_response
from utils.db_pool import get_pool
from utils.data_archiving import get_data_statistics, archive_all
from utils.login_security import get_login_security_manager
from utils.cache import get_cache

# Blueprint 생성
health_api = Blueprint('health_api', __name__, url_prefix='/api/health')

# 앱 시작 시간
_app_start_time = time.time()


@health_api.route("", methods=["GET"])
def health_check():
    """기본 헬스 체크 (인증 불필요).
    
    Returns:
        상태, 업타임, 타임스탬프
    """
    uptime_seconds = int(time.time() - _app_start_time)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": {
            "seconds": uptime_seconds,
            "formatted": f"{uptime_hours}시간 {uptime_minutes}분"
        }
    }), 200


@health_api.route("/detailed", methods=["GET"])
@require_auth
def detailed_health_check():
    """상세 헬스 체크 (인증 필요).
    
    Returns:
        시스템 리소스, DB 상태, 캐시 상태 등
    """
    # 시스템 리소스
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # DB 연결 테스트
    db_healthy = True
    db_error = None
    try:
        pool = get_pool()
        pool.execute("SELECT 1")
    except Exception as e:
        db_healthy = False
        db_error = str(e)
    
    # 캐시 통계
    cache = get_cache()
    cache_stats = cache.get_stats()
    
    # 업타임
    uptime_seconds = int(time.time() - _app_start_time)
    
    return success_response(
        data={
            "status": "healthy" if db_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime_seconds,
            "system": {
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_available_mb": round(memory.available / (1024 * 1024), 1),
                "disk_percent": round(disk.percent, 1),
                "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 1)
            },
            "database": {
                "healthy": db_healthy,
                "error": db_error
            },
            "cache": {
                "hit_rate": cache_stats.get("hit_rate", 0),
                "size": cache_stats.get("cache_size", 0)
            }
        }
    )


@health_api.route("/database", methods=["GET"])
@require_auth
@require_admin
def database_health():
    """데이터베이스 헬스 체크 (관리자만).
    
    Returns:
        DB 통계, 테이블 크기, 데이터 수 등
    """
    stats = get_data_statistics()
    
    return success_response(
        data=stats,
        message="데이터베이스 통계 조회 성공"
    )


@health_api.route("/security", methods=["GET"])
@require_auth
@require_admin
def security_status():
    """보안 상태 조회 (관리자만).
    
    Returns:
        잠긴 계정 목록, 로그인 시도 통계 등
    """
    security_manager = get_login_security_manager()
    locked_accounts = security_manager.get_locked_accounts()
    
    return success_response(
        data={
            "locked_accounts": locked_accounts,
            "locked_count": len(locked_accounts)
        },
        message="보안 상태 조회 성공"
    )


@health_api.route("/archive", methods=["POST"])
@require_auth
@require_admin
def trigger_archiving():
    """데이터 아카이빙 수동 실행 (관리자만).
    
    Returns:
        아카이빙 결과
    """
    result = archive_all()
    
    return success_response(
        data=result,
        message=f"아카이빙 완료: {result['total_saved_mb']}MB 절약"
    )


@health_api.route("/unlock/<username>", methods=["POST"])
@require_auth
@require_admin
def unlock_account(username: str):
    """계정 잠금 해제 (관리자만).
    
    Args:
        username: 사용자명
    
    Returns:
        해제 결과
    """
    security_manager = get_login_security_manager()
    success = security_manager.unlock_account(username)
    
    if success:
        return success_response(
            message=f"계정 '{username}' 잠금이 해제되었습니다"
        )
    else:
        return success_response(
            message=f"계정 '{username}'은 잠겨있지 않습니다"
        )
