"""프로덕션 서버 실행 스크립트 (Waitress WSGI 서버).

개발 모드에서는 Flask 내장 서버를 사용하고,
프로덕션 모드에서는 Waitress WSGI 서버를 사용합니다.
"""

from waitress import serve
from app import app
from config import Config

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Monitoring System - 프로덕션 서버 시작")
    print("=" * 60)
    print(f"📍 서버 주소: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    print(f"🔒 디버그 모드: OFF")
    print(f"⚡ WSGI 서버: Waitress")
    print(f"🧵 스레드 수: 4")
    print(f"📦 프론트엔드: 빌드된 정적 파일 서빙")
    print("=" * 60)
    print("✅ 서버가 시작되었습니다. Ctrl+C로 종료할 수 있습니다.")
    print("=" * 60)
    print()
    
    # Waitress 서버 실행
    serve(
        app,
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        threads=4,              # 동시 처리 스레드 수
        url_scheme='http',
        channel_timeout=120,    # 채널 타임아웃 (초)
        cleanup_interval=30,    # 정리 간격 (초)
        asyncore_use_poll=True  # Windows에서 성능 향상
    )
