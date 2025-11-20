"""프로덕션 서버 실행 스크립트 (Waitress)."""

from waitress import serve
from app import app
import os

if __name__ == '__main__':
    # 환경 변수에서 설정 읽기
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    
    print("=" * 60)
    print("🚀 프로그램 모니터링 시스템 - 프로덕션 서버 시작")
    print("=" * 60)
    print(f"📍 서버 주소: http://{host}:{port}")
    print(f"🔒 디버그 모드: OFF")
    print(f"⚡ WSGI 서버: Waitress")
    print(f"🧵 스레드 수: 4")
    print("=" * 60)
    print("✅ 서버가 시작되었습니다. Ctrl+C로 종료할 수 있습니다.")
    print("=" * 60)
    
    # Waitress 서버 실행
    serve(
        app,
        host=host,
        port=port,
        threads=4,  # 동시 처리 스레드 수
        url_scheme='http',
        channel_timeout=120,  # 채널 타임아웃 (초)
        cleanup_interval=30,  # 정리 간격 (초)
        asyncore_use_poll=True  # Windows에서 성능 향상
    )
