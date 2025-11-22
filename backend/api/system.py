"""시스템 모니터링 API 엔드포인트."""

from flask import Blueprint, jsonify
import psutil
from utils.decorators import require_auth
from utils.responses import success_response

# Blueprint 생성
system_api = Blueprint('system_api', __name__, url_prefix='/api/system')


@system_api.route('/stats', methods=['GET'])
@require_auth
def get_system_stats():
    """시스템 통계 조회 API.
    
    Returns:
        JSON: {
            "stats": {
                "cpu_percent": CPU 사용률 (0-100),
                "memory_percent": 메모리 사용률 (0-100),
                "memory_mb": 사용 중인 메모리 (MB),
                "memory_total_mb": 전체 메모리 (MB),
                "disk_percent": 디스크 사용률 (0-100),
                "disk_free_gb": 여유 디스크 (GB),
                "disk_total_gb": 전체 디스크 (GB),
                "uptime_seconds": 시스템 가동 시간 (초)
            }
        }
    """
    try:
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 메모리 정보
        memory = psutil.virtual_memory()
        memory_mb = memory.used / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)
        memory_percent = memory.percent
        
        # 디스크 정보 (C: 드라이브)
        try:
            disk = psutil.disk_usage('C:\\')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            disk_total_gb = disk.total / (1024 * 1024 * 1024)
        except Exception:
            # 디스크 정보 조회 실패 시 기본값
            disk_percent = 0
            disk_free_gb = 0
            disk_total_gb = 0
        
        # 시스템 부팅 시간
        boot_time = psutil.boot_time()
        import time
        uptime_seconds = int(time.time() - boot_time)
        
        stats = {
            'cpu_percent': round(cpu_percent, 2),
            'memory_percent': round(memory_percent, 2),
            'memory_mb': round(memory_mb, 2),
            'memory_total_mb': round(memory_total_mb, 2),
            'disk_percent': round(disk_percent, 2),
            'disk_free_gb': round(disk_free_gb, 2),
            'disk_total_gb': round(disk_total_gb, 2),
            'uptime_seconds': uptime_seconds
        }
        
        return jsonify(success_response(stats, 'stats'))
        
    except Exception as e:
        print(f"⚠️ [System API] 시스템 통계 조회 오류: {str(e)}")
        return jsonify({
            'error': '시스템 통계를 조회할 수 없습니다',
            'message': str(e)
        }), 500


@system_api.route('/health', methods=['GET'])
@require_auth
def health_check():
    """헬스 체크 API.
    
    Returns:
        JSON: {"status": "healthy"}
    """
    return jsonify({'status': 'healthy'}), 200
