"""프로그램 메트릭 조회 API."""

from flask import Blueprint, jsonify, session
from utils.database import get_resource_usage

metrics_api = Blueprint('metrics_api', __name__, url_prefix='/api/metrics')


@metrics_api.route('/<int:program_id>', methods=['GET'])
def get_program_metrics(program_id):
    """프로그램의 리소스 사용량 기록 조회.
    
    Args:
        program_id: 프로그램 ID
        
    Query Parameters:
        hours: 조회할 시간 범위 (기본: 24시간)
        
    Returns:
        JSON: {
            "metrics": [
                {
                    "id": 1,
                    "program_id": 1,
                    "cpu_percent": 15.5,
                    "memory_mb": 128.3,
                    "timestamp": "2024-01-01 12:00:00"
                },
                ...
            ]
        }
    """
    # 인증 확인
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    from flask import request
    hours = request.args.get('hours', default=24, type=int)
    
    # 최대 7일(168시간)로 제한
    if hours > 168:
        hours = 168
    
    try:
        metrics = get_resource_usage(program_id, hours=hours)
        return jsonify({"metrics": metrics}), 200
    except Exception as e:
        print(f"[Metrics API] 메트릭 조회 오류: {str(e)}")
        return jsonify({"error": str(e)}), 500
