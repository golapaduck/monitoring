"""프로덕션 서버 실행 스크립트 (Waitress WSGI 서버).

개발 모드에서는 Flask 내장 서버를 사용하고,
프로덕션 모드에서는 Waitress WSGI 서버를 사용합니다.
"""

import os
import multiprocessing
from waitress import serve
from app import app
from config import Config

# CPU 코어 수 기반 최적 스레드 수 계산
CPU_COUNT = multiprocessing.cpu_count()
OPTIMAL_THREADS = max(4, CPU_COUNT * 2)  # 최소 4, 권장 CPU * 2

# 환경 변수에서 설정 읽기 (오버라이드 가능)
THREADS = int(os.getenv('WAITRESS_THREADS', OPTIMAL_THREADS))
CHANNEL_TIMEOUT = int(os.getenv('WAITRESS_CHANNEL_TIMEOUT', '120'))
CONNECTION_LIMIT = int(os.getenv('WAITRESS_CONNECTION_LIMIT', '100'))
RECV_BYTES = int(os.getenv('WAITRESS_RECV_BYTES', '8192'))
SEND_BYTES = int(os.getenv('WAITRESS_SEND_BYTES', '8192'))

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Monitoring System - 프로덕션 서버 시작 (Waitress WSGI)")
    print("=" * 70)
    print(f"📍 서버 주소: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    print(f"🔒 디버그 모드: OFF")
    print(f"⚡ WSGI 서버: Waitress (최적화됨)")
    print(f"💻 CPU 코어: {CPU_COUNT}개")
    print(f"🧵 워커 스레드: {THREADS}개")
    print(f"🔗 최대 연결: {CONNECTION_LIMIT}개")
    print(f"⏱️ 채널 타임아웃: {CHANNEL_TIMEOUT}초")
    print(f"📦 프론트엔드: 빌드된 정적 파일 서빙")
    print(f"🌐 웹소켓: Socket.IO 지원")
    print("=" * 70)
    print("✅ 서버가 시작되었습니다. Ctrl+C로 종료할 수 있습니다.")
    print("=" * 70)
    print()
    
    # Waitress 서버 실행 (최적화된 설정)
    serve(
        app,
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        
        # 스레드 설정
        threads=THREADS,                    # CPU 기반 최적 스레드 수
        
        # 연결 설정
        connection_limit=CONNECTION_LIMIT,  # 최대 동시 연결 수
        channel_timeout=CHANNEL_TIMEOUT,    # 채널 타임아웃 (초)
        
        # 버퍼 설정 (성능 최적화)
        recv_bytes=RECV_BYTES,              # 수신 버퍼 크기 (8KB)
        send_bytes=SEND_BYTES,              # 송신 버퍼 크기 (8KB)
        
        # 타임아웃 설정
        cleanup_interval=30,                # 정리 간격 (초)
        
        # 플랫폼 최적화
        asyncore_use_poll=True,             # Windows에서 성능 향상
        
        # URL 스킴
        url_scheme='http',
        
        # 로깅
        _quiet=False,                       # 로그 출력
        _profile=False,                     # 프로파일링 비활성화
        
        # 백로그 (대기 큐 크기)
        backlog=1024,                       # 연결 대기 큐
        
        # 소켓 옵션
        ipv4=True,                          # IPv4 사용
        ipv6=False,                         # IPv6 비활성화 (필요시 True)
    )
