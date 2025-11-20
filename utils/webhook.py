"""웹훅 알림 유틸리티."""

import requests
import json
import threading
from datetime import datetime
from pathlib import Path
from utils.data_manager import load_json, save_json
from config import DATA_DIR


# 웹훅 설정 파일 경로
WEBHOOK_CONFIG_JSON = DATA_DIR / "webhook_config.json"
WEBHOOK_THREADS_JSON = DATA_DIR / "webhook_threads.json"


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


def get_thread_id(program_name):
    """프로그램의 Discord 스레드 ID 조회.
    
    Args:
        program_name: 프로그램 이름
        
    Returns:
        str or None: 스레드 ID (없으면 None)
    """
    threads = load_json(WEBHOOK_THREADS_JSON, {})
    return threads.get(program_name)


def save_thread_id(program_name, thread_id):
    """프로그램의 Discord 스레드 ID 저장.
    
    Args:
        program_name: 프로그램 이름
        thread_id: Discord 스레드 ID
    """
    threads = load_json(WEBHOOK_THREADS_JSON, {})
    threads[program_name] = thread_id
    save_json(WEBHOOK_THREADS_JSON, threads)
    print(f"💾 [Webhook] 스레드 ID 저장: {program_name} -> {thread_id}")


def _send_webhook_sync(program_name, event_type, details="", status="info", webhook_url=None):
    """웹훅 알림 전송 (동기 버전 - 내부 사용).
    
    Args:
        program_name: 프로그램 이름
        event_type: 이벤트 타입 ('start', 'stop', 'restart', 'crash')
        details: 추가 상세 정보
        status: 알림 상태 ('info', 'success', 'warning', 'error')
        webhook_url: 프로그램별 웹훅 URL
        
    Returns:
        tuple: (성공 여부, 메시지)
    """
    config = get_webhook_config()
    
    # 프로그램별 웹훅 URL이 없으면 스킵 (전역 설정 사용 안 함)
    if not webhook_url:
        return True, "No program-specific webhook configured"
    
    target_url = webhook_url
    
    # 웹훅이 비활성화되어 있으면 스킵
    if not config.get("enabled"):
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
    is_discord = "discord.com" in target_url.lower()
    
    if is_discord:
        # 기존 스레드 ID 확인
        thread_id = get_thread_id(program_name)
        
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
        
        # 스레드 이름 설정 (새 스레드 생성 시에만)
        if not thread_id:
            payload["thread_name"] = f"🖥️ {program_name}"
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
        # Discord 포럼 채널의 경우 thread_id를 URL 쿼리 파라미터로 전달
        request_url = target_url
        if is_discord and thread_id:
            # 기존 스레드에 메시지 추가 (쿼리 파라미터 사용)
            request_url = f"{target_url}?thread_id={thread_id}"
            # payload에서 thread_id 제거 (URL에 포함되므로)
            payload.pop('thread_id', None)
            print(f"🔄 [Webhook] 기존 스레드에 메시지 추가: {program_name} (ID: {thread_id})")
        elif is_discord and 'thread_name' in payload:
            print(f"🆕 [Webhook] 새 스레드 생성: {payload['thread_name']}")
        
        # 디버깅: 전송하는 페이로드 출력
        print(f"📤 [Webhook] 요청 URL: {request_url[:80]}...")
        print(f"📤 [Webhook] 페이로드 키: {list(payload.keys())}")
        
        # 웹훅 URL로 POST 요청
        response = requests.post(
            request_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ [Webhook] 알림 전송 성공: {program_name} - {event_type}")
            
            # Discord 응답에서 새로 생성된 스레드 ID 추출 및 저장
            if is_discord and not thread_id:
                try:
                    # 204 No Content는 응답 본문이 없음
                    if response.status_code != 204 and response.text:
                        response_data = response.json()
                        print(f"📥 [Webhook] Discord 응답 전체:")
                        print(f"   {json.dumps(response_data, indent=2)[:500]}")
                        
                        extracted_thread_id = None
                        
                        # 여러 가능한 위치에서 스레드 ID 찾기
                        # 1. thread.id (포럼 채널 응답)
                        if "thread" in response_data:
                            if isinstance(response_data["thread"], dict) and "id" in response_data["thread"]:
                                extracted_thread_id = response_data["thread"]["id"]
                                print(f"✓ [Webhook] thread.id에서 발견: {extracted_thread_id}")
                        
                        # 2. channel_id (일부 응답)
                        if not extracted_thread_id and "channel_id" in response_data:
                            extracted_thread_id = response_data["channel_id"]
                            print(f"✓ [Webhook] channel_id에서 발견: {extracted_thread_id}")
                        
                        # 3. id (직접 응답)
                        if not extracted_thread_id and "id" in response_data:
                            extracted_thread_id = response_data["id"]
                            print(f"✓ [Webhook] id에서 발견: {extracted_thread_id}")
                        
                        if extracted_thread_id:
                            save_thread_id(program_name, extracted_thread_id)
                        else:
                            print(f"⚠️ [Webhook] 응답에서 스레드 ID를 찾을 수 없음")
                            print(f"   응답 키: {list(response_data.keys())}")
                    else:
                        print(f"ℹ️ [Webhook] 204 No Content - 스레드 ID 없음")
                except Exception as e:
                    print(f"⚠️ [Webhook] 스레드 ID 추출 실패: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            return True, "Webhook sent successfully"
        else:
            error_msg = f"Webhook failed with status {response.status_code}"
            print(f"❌ [Webhook Error] {error_msg}")
            print(f"   - URL: {target_url[:50]}...")
            print(f"   - Response: {response.text[:200]}")
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "Webhook request timeout"
        print(f"⏱️ [Webhook Timeout] {error_msg}")
        print(f"   - URL: {target_url[:50]}...")
        return False, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Webhook request failed: {str(e)}"
        print(f"🔌 [Webhook Connection Error] {error_msg}")
        print(f"   - URL: {target_url[:50]}...")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"💥 [Webhook Unexpected Error] {error_msg}")
        print(f"   - Program: {program_name}")
        print(f"   - Event: {event_type}")
        return False, error_msg


def send_webhook_notification(program_name, event_type, details="", status="info", webhook_url=None):
    """웹훅 알림 전송 (비동기 처리).
    
    백그라운드 스레드에서 웹훅을 전송하여 메인 프로세스를 블로킹하지 않습니다.
    
    Args:
        program_name: 프로그램 이름
        event_type: 이벤트 타입 ('start', 'stop', 'restart', 'crash')
        details: 추가 상세 정보
        status: 알림 상태 ('info', 'success', 'warning', 'error')
        webhook_url: 프로그램별 웹훅 URL
        
    Returns:
        tuple: (True, "Webhook queued") - 즉시 반환
    """
    # 웹훅이 설정되지 않았으면 스킵
    if not webhook_url:
        return True, "No program-specific webhook configured"
    
    # 백그라운드 스레드에서 웹훅 전송
    thread = threading.Thread(
        target=_send_webhook_sync,
        args=(program_name, event_type, details, status, webhook_url),
        daemon=True,
        name=f"Webhook-{program_name}-{event_type}"
    )
    thread.start()
    
    print(f"🚀 [Webhook] 비동기 전송 시작: {program_name} - {event_type}")
    return True, "Webhook queued for async delivery"


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
            }],
            "thread_name": "🧪 웹훅 테스트"  # 포럼 채널 지원
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
        print(f"🧪 [Webhook Test] 테스트 시작...")
        print(f"   - URL: {url[:50]}...")
        
        response = requests.post(
            url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"✅ [Webhook Test] 테스트 성공! (상태 코드: {response.status_code})")
            return True, f"테스트 성공! (상태 코드: {response.status_code})"
        else:
            error_msg = f"테스트 실패 (상태 코드: {response.status_code})"
            print(f"❌ [Webhook Test Error] {error_msg}")
            print(f"   - Response: {response.text[:200]}")
            return False, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "요청 시간 초과 (5초)"
        print(f"⏱️ [Webhook Test Timeout] {error_msg}")
        return False, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"연결 실패: {str(e)}"
        print(f"🔌 [Webhook Test Connection Error] {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"오류 발생: {str(e)}"
        print(f"💥 [Webhook Test Unexpected Error] {error_msg}")
        return False, error_msg
