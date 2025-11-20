"""프로그램 실행 로그 및 통계 관리 유틸리티."""

from datetime import datetime
from pathlib import Path
from utils.data_manager import load_json, save_json
from config import DATA_DIR


# 로그 파일 경로
LOGS_JSON = DATA_DIR / "logs.json"


def log_program_event(program_name, event_type, details=""):
    """프로그램 이벤트 로그 기록.
    
    Args:
        program_name: 프로그램 이름
        event_type: 이벤트 타입 ('start', 'stop', 'restart', 'crash')
        details: 추가 상세 정보
    """
    logs_data = load_json(LOGS_JSON, {"logs": []})
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "program_name": program_name,
        "event_type": event_type,
        "details": details
    }
    
    logs_data["logs"].append(log_entry)
    
    # 최근 1000개 로그만 유지
    if len(logs_data["logs"]) > 1000:
        logs_data["logs"] = logs_data["logs"][-1000:]
    
    save_json(LOGS_JSON, logs_data)


def get_program_logs(program_name=None, limit=100):
    """프로그램 로그 조회.
    
    Args:
        program_name: 특정 프로그램 이름 (None이면 전체 조회)
        limit: 조회할 로그 개수
        
    Returns:
        list: 로그 목록 (최신순)
    """
    logs_data = load_json(LOGS_JSON, {"logs": []})
    logs = logs_data["logs"]
    
    # 특정 프로그램 필터링
    if program_name:
        logs = [log for log in logs if log["program_name"] == program_name]
    
    # 최신순 정렬 및 limit 적용
    logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)
    return logs[:limit]


def get_program_stats(program_name):
    """프로그램 통계 조회.
    
    Args:
        program_name: 프로그램 이름
        
    Returns:
        dict: {
            'total_starts': 총 시작 횟수,
            'total_stops': 총 종료 횟수,
            'total_restarts': 총 재시작 횟수,
            'last_start': 마지막 시작 시간,
            'last_stop': 마지막 종료 시간
        }
    """
    logs = get_program_logs(program_name, limit=None)
    
    stats = {
        'total_starts': 0,
        'total_stops': 0,
        'total_restarts': 0,
        'last_start': None,
        'last_stop': None
    }
    
    for log in logs:
        if log['event_type'] == 'start':
            stats['total_starts'] += 1
            if not stats['last_start']:
                stats['last_start'] = log['timestamp']
        elif log['event_type'] == 'stop':
            stats['total_stops'] += 1
            if not stats['last_stop']:
                stats['last_stop'] = log['timestamp']
        elif log['event_type'] == 'restart':
            stats['total_restarts'] += 1
    
    return stats


def calculate_uptime(program_name):
    """프로그램 가동 시간 계산.
    
    Args:
        program_name: 프로그램 이름
        
    Returns:
        dict: {
            'is_running': 현재 실행 중 여부,
            'uptime_seconds': 가동 시간 (초),
            'uptime_formatted': 가동 시간 (포맷팅)
        }
    """
    logs = get_program_logs(program_name, limit=None)
    
    # 최근 시작/종료 이벤트 찾기
    last_start = None
    last_stop = None
    
    for log in logs:
        if log['event_type'] == 'start' and not last_start:
            last_start = datetime.fromisoformat(log['timestamp'])
        elif log['event_type'] == 'stop' and not last_stop:
            last_stop = datetime.fromisoformat(log['timestamp'])
    
    # 현재 실행 중인지 확인 (마지막 start가 마지막 stop보다 최근)
    is_running = last_start and (not last_stop or last_start > last_stop)
    
    if is_running:
        uptime_seconds = (datetime.now() - last_start).total_seconds()
        
        # 포맷팅
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        if hours > 0:
            uptime_formatted = f"{hours}시간 {minutes}분"
        elif minutes > 0:
            uptime_formatted = f"{minutes}분 {seconds}초"
        else:
            uptime_formatted = f"{seconds}초"
        
        return {
            'is_running': True,
            'uptime_seconds': int(uptime_seconds),
            'uptime_formatted': uptime_formatted
        }
    else:
        return {
            'is_running': False,
            'uptime_seconds': 0,
            'uptime_formatted': '중지됨'
        }
