"""웹훅 알림 유틸리티."""

import requests
import json
from datetime import datetime
from pathlib import Path
from utils.data_manager import load_json, save_json
from config import DATA_DIR


# 웹훅 설정 파일 경로
WEBHOOK_CONFIG_JSON = DATA_DIR / "webhook_config.json"


def get_webhook_config():
    """웹훅 설정 조회.
    
    Returns:
        dict: {
            'enabled': 웹훅 활성화 여부,
            'url': 웹훅 URL,
            'events': 알림받을 이벤트 목록 ['start', 'stop', 'restart', 'crash']
        }
    """
    default_config = {
        "enabled": False,
        "url": "",
        "events": ["start", "stop", "restart"]
    }
    return load_json(WEBHOOK_CONFIG_JSON, default_config)


def save_webhook_config(config):
    """웹훅 설정 저장.
    
    Args:
        config: 웹훅 설정 딕셔너리
    """
    save_json(WEBHOOK_CONFIG_JSON, config)


def send_webhook_notification(program_name, event_type, details="", status="info"):
    """웹훅 알림 전송 (Discord Embed 형식 지원).
    
    Args:
        program_name: 프로그램 이름
        event_type: 이벤트 타입 ('start', 'stop', 'restart', 'crash')
        details: 추가 상세 정보
        status: 알림 상태 ('info', 'success', 'warning', 'error')
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    config = get_webhook_config()
    
    # 웹훅이 비활성화되어 있거나 URL이 없으면 스킵
    if not config.get("enabled") or not config.get("url"):
        return True, "Webhook disabled"
    
    # 이벤트 타입이 설정된 이벤트 목록에 없으면 스킵
    if event_type not in config.get("events", []):
        return True, f"Event type '{event_type}' not in configured events"
    
    # 이벤트별 색상 및 이모지 설정
    event_config = {
        "start": {
            "color": 3066993,  # 녹색
            "emoji": "▶️",
            "title": "프로그램 시작",
            "description": f"**{program_name}** 프로그램이 시작되었습니다."
        },
        "stop": {
            "color": 15158332,  # 빨강
            "emoji": "⏹️",
            "title": "프로그램 종료",
            "description": f"**{program_name}** 프로그램이 종료되었습니다."
        },
        "restart": {
            "color": 15844367,  # 주황
            "emoji": "🔄",
            "title": "프로그램 재시작",
            "description": f"**{program_name}** 프로그램이 재시작되었습니다."
        },
        "crash": {
            "color": 10038562,  # 진한 빨강
            "emoji": "❌",
            "title": "프로그램 크래시",
            "description": f"**{program_name}** 프로그램에 오류가 발생했습니다."
        }
    }
    
    config_data = event_config.get(event_type, {
        "color": 3447003,  # 파랑
        "emoji": "ℹ️",
        "title": "알림",
        "description": f"**{program_name}** - {event_type}"
    })
    
    # Discord 웹훅인지 확인 (URL에 discord.com 포함 여부)
    is_discord = "discord.com" in config["url"].lower()
    
    if is_discord:
        # Discord Embed 형식
        payload = {
            "content": f"{config_data['emoji']} {config_data['title']}",
            "embeds": [{
                "description": config_data['description'],
                "color": config_data['color'],
                "fields": [
                    {
                        "name": "📋 상세 정보",
                        "value": details if details else "없음",
                        "inline": False
                    },
                    {
                        "name": "⏰ 시간",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "inline": True
                    },
                    {
                        "name": "📊 상태",
                        "value": status.upper(),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "프로그램 모니터링 시스템"
                },
                "timestamp": datetime.now().isoformat()
            }]
        }
    else:
        # 일반 웹훅 형식 (기존 방식)
        payload = {
            "program_name": program_name,
            "event_type": event_type,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "message": f"프로그램 '{program_name}' - {event_type}"
        }
    
    try:
        # 웹훅 URL로 POST 요청
        response = requests.post(
            config["url"],
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code in [200, 201, 204]:
            return True, "Webhook sent successfully"
        else:
            return False, f"Webhook failed with status {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Webhook request timeout"
    except requests.exceptions.RequestException as e:
        return False, f"Webhook request failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def test_webhook(url):
    """웹훅 URL 테스트 (Discord Embed 형식 지원).
    
    Args:
        url: 테스트할 웹훅 URL
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    # Discord 웹훅인지 확인
    is_discord = "discord.com" in url.lower()
    
    if is_discord:
        # Discord Embed 형식 테스트 메시지
        test_payload = {
            "content": "✅ 웹훅 연결 테스트",
            "embeds": [{
                "description": "**프로그램 모니터링 시스템**과 Discord가 성공적으로 연결되었습니다!",
                "color": 5763719,  # 청록색
                "fields": [
                    {
                        "name": "🔔 알림 설정",
                        "value": "이제 프로그램 시작/종료/재시작 알림을 받을 수 있습니다.",
                        "inline": False
                    },
                    {
                        "name": "⏰ 테스트 시간",
                        "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "inline": True
                    },
                    {
                        "name": "📊 상태",
                        "value": "정상",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "프로그램 모니터링 시스템"
                },
                "timestamp": datetime.now().isoformat()
            }]
        }
    else:
        # 일반 웹훅 형식
        test_payload = {
            "program_name": "Test Program",
            "event_type": "test",
            "status": "info",
            "details": "웹훅 연결 테스트",
            "timestamp": datetime.now().isoformat(),
            "message": "웹훅 테스트 메시지입니다."
        }
    
    try:
        response = requests.post(
            url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code in [200, 201, 204]:
            return True, f"테스트 성공! (상태 코드: {response.status_code})"
        else:
            return False, f"테스트 실패 (상태 코드: {response.status_code})"
            
    except requests.exceptions.Timeout:
        return False, "요청 시간 초과 (5초)"
    except requests.exceptions.RequestException as e:
        return False, f"연결 실패: {str(e)}"
    except Exception as e:
        return False, f"오류 발생: {str(e)}"
