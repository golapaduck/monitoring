"""작업 큐 API 엔드포인트."""

from flask import Blueprint, jsonify
import logging
from utils.job_queue import get_job_queue
from utils.decorators import require_auth

logger = logging.getLogger(__name__)

# Blueprint 생성
jobs_api = Blueprint('jobs_api', __name__, url_prefix='/api/jobs')


@jobs_api.route("", methods=["GET"])
@require_auth
def list_jobs():
    """모든 작업 조회 API."""
    try:
        queue = get_job_queue()
        jobs = queue.get_all_jobs()
        
        return jsonify({
            "jobs": jobs,
            "total": len(jobs)
        })
    except Exception as e:
        logger.error(f"작업 목록 조회 실패: {str(e)}")
        return jsonify({
            "error": "작업 목록 조회 실패",
            "message": str(e)
        }), 500


@jobs_api.route("/<job_id>", methods=["GET"])
@require_auth
def get_job(job_id):
    """특정 작업 조회 API.
    
    Args:
        job_id: 작업 ID
    """
    try:
        queue = get_job_queue()
        job = queue.get_job(job_id)
        
        if not job:
            return jsonify({
                "error": "작업을 찾을 수 없습니다"
            }), 404
        
        return jsonify(job.to_dict())
    except Exception as e:
        logger.error(f"작업 조회 실패: {str(e)}")
        return jsonify({
            "error": "작업 조회 실패",
            "message": str(e)
        }), 500
