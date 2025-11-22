"""웹소켓 실시간 업데이트 시스템.

프로그램 상태 변경, 리소스 사용량 등을 실시간으로 클라이언트에 전송합니다.
"""

from flask_socketio import SocketIO, emit
from flask import request

# SocketIO 인스턴스 (app.py에서 초기화)
socketio = None


def init_socketio(app):
    """SocketIO 초기화.
    
    Args:
        app: Flask 애플리케이션 인스턴스
        
    Returns:
        SocketIO: 초기화된 SocketIO 인스턴스
    """
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # 개발 시 모든 origin 허용
        async_mode='threading',     # threading 모드 사용
        logger=False,               # 로깅 비활성화 (선택)
        engineio_logger=False       # Engine.IO 로깅 비활성화
    )
    
    # 이벤트 핸들러 등록
    register_handlers()
    
    print("🔌 [WebSocket] SocketIO 초기화 완료")
    return socketio


def register_handlers():
    """웹소켓 이벤트 핸들러 등록."""
    
    @socketio.on('connect')
    def handle_connect():
        """클라이언트 연결 시."""
        print(f"🔌 [WebSocket] 클라이언트 연결: {request.sid}")
        emit('connected', {'message': '웹소켓 연결 성공'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """클라이언트 연결 해제 시."""
        print(f"🔌 [WebSocket] 클라이언트 연결 해제: {request.sid}")
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        """특정 이벤트 구독.
        
        Args:
            data: {'event': 'program_status'} 형태
        """
        event_type = data.get('event')
        print(f"🔌 [WebSocket] 구독 요청: {event_type} (클라이언트: {request.sid})")
        emit('subscribed', {'event': event_type, 'status': 'success'})


def emit_program_status(program_id, status_data):
    """프로그램 상태 변경 이벤트 전송.
    
    Args:
        program_id: 프로그램 ID
        status_data: 상태 데이터 (running, pid 등)
    """
    if socketio:
        print(f"🔌 [WebSocket] 프로그램 상태 전송: ID={program_id}, data={status_data}")
        socketio.emit('program_status', {
            'program_id': program_id,
            'data': status_data
        })
    else:
        print("⚠️ [WebSocket] SocketIO가 초기화되지 않음")


def emit_resource_update(program_id, metrics):
    """리소스 사용량 업데이트 이벤트 전송.
    
    Args:
        program_id: 프로그램 ID
        metrics: 리소스 메트릭 (cpu, memory 등)
    """
    if socketio:
        socketio.emit('resource_update', {
            'program_id': program_id,
            'metrics': metrics
        })


def emit_program_list_update():
    """프로그램 목록 업데이트 이벤트 전송."""
    if socketio:
        socketio.emit('program_list_update', {
            'message': '프로그램 목록이 업데이트되었습니다'
        })


def emit_notification(notification_type, message, data=None):
    """일반 알림 이벤트 전송.
    
    Args:
        notification_type: 알림 타입 (info, warning, error, success)
        message: 알림 메시지
        data: 추가 데이터 (선택)
    """
    if socketio:
        socketio.emit('notification', {
            'type': notification_type,
            'message': message,
            'data': data or {}
        })


def get_socketio():
    """SocketIO 인스턴스 반환.
    
    Returns:
        SocketIO: SocketIO 인스턴스 또는 None
    """
    return socketio
