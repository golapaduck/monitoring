"""데이터 관리 유틸리티 함수들 (JSON 파일 처리)."""

import json
from pathlib import Path


def load_json(filepath, default=None):
    """JSON 파일을 읽어서 반환. 파일이 없으면 기본값 반환.
    
    Args:
        filepath: JSON 파일 경로 (Path 객체)
        default: 파일이 없을 때 반환할 기본값
        
    Returns:
        dict: JSON 데이터 또는 기본값
    """
    if not filepath.exists():
        return default if default is not None else {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default if default is not None else {}


def save_json(filepath, data):
    """데이터를 JSON 파일로 저장.
    
    Args:
        filepath: JSON 파일 경로 (Path 객체)
        data: 저장할 데이터 (dict)
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_default_data(users_json, programs_json, status_json):
    """초기 기본 데이터 생성 (사용자, 프로그램 목록 등).
    
    Args:
        users_json: 사용자 JSON 파일 경로
        programs_json: 프로그램 JSON 파일 경로
        status_json: 상태 JSON 파일 경로
    """
    
    # 기본 사용자 생성
    if not users_json.exists():
        users_data = {
            "users": [
                {"username": "admin", "password": "admin", "role": "admin"},
                {"username": "guest", "password": "guest", "role": "guest"}
            ]
        }
        save_json(users_json, users_data)
    
    # 기본 프로그램 목록 생성
    if not programs_json.exists():
        programs_data = {
            "programs": []
        }
        save_json(programs_json, programs_data)
    
    # 기본 상태 데이터 생성
    if not status_json.exists():
        status_data = {
            "last_update": "",
            "programs_status": []
        }
        save_json(status_json, status_data)
