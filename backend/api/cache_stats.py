"""캐시 통계 API 엔드포인트."""

from flask import Blueprint, jsonify
from utils.decorators import require_auth, require_admin
from utils.cache import get_cache
from utils.responses import success_response

# Blueprint 생성
cache_stats_api = Blueprint('cache_stats_api', __name__, url_prefix='/api/cache')


@cache_stats_api.route("/stats", methods=["GET"])
@require_auth
@require_admin
def get_cache_stats():
    """캐시 통계 조회 (관리자만).
    
    Returns:
        캐시 히트율, 요청 수, 캐시 크기 등
    """
    cache = get_cache()
    stats = cache.get_stats()
    
    return success_response(
        data=stats,
        message="캐시 통계 조회 성공"
    )


@cache_stats_api.route("/clear", methods=["POST"])
@require_auth
@require_admin
def clear_cache():
    """캐시 전체 삭제 (관리자만)."""
    cache = get_cache()
    cache.clear()
    
    return success_response(
        message="캐시가 전체 삭제되었습니다"
    )


@cache_stats_api.route("/stats/reset", methods=["POST"])
@require_auth
@require_admin
def reset_cache_stats():
    """캐시 통계 초기화 (관리자만)."""
    cache = get_cache()
    cache.reset_stats()
    
    return success_response(
        message="캐시 통계가 초기화되었습니다"
    )


@cache_stats_api.route("/invalidate/<tag>", methods=["POST"])
@require_auth
@require_admin
def invalidate_by_tag(tag: str):
    """태그로 캐시 무효화 (관리자만).
    
    Args:
        tag: 무효화할 태그
    """
    cache = get_cache()
    invalidated = cache.invalidate_by_tag(tag)
    
    return success_response(
        data={"invalidated": invalidated},
        message=f"{invalidated}개의 캐시가 무효화되었습니다"
    )
