#!/usr/bin/env python3
"""모니터링 시스템 실행 스크립트.

개발/프로덕션 모드를 선택하여 실행할 수 있습니다.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def run_dev():
    """개발 모드 실행 (Flask + Vite)."""
    print("\n" + "=" * 70)
    print("🚀 Monitoring System - Development Mode")
    print("=" * 70)
    print()
    
    # 환경 변수 설정
    os.environ['PRODUCTION'] = 'False'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = 'True'
    
    print("📝 환경 변수 설정:")
    print("  - PRODUCTION=False")
    print("  - FLASK_ENV=development")
    print("  - FLASK_DEBUG=True")
    print()
    
    # 백엔드 프로세스
    print("🔧 백엔드 시작 중...")
    backend_process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("✅ 백엔드 시작됨 (PID: {})".format(backend_process.pid))
    print()
    
    # 프론트엔드 프로세스
    print("🎨 프론트엔드 시작 중...")
    frontend_process = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    print("✅ 프론트엔드 시작됨 (PID: {})".format(frontend_process.pid))
    print()
    
    print("=" * 70)
    print("📍 프론트엔드: http://localhost:5173")
    print("📍 백엔드: http://localhost:8080")
    print()
    print("종료하려면: Ctrl + C")
    print("=" * 70)
    print()
    
    try:
        # 두 프로세스가 모두 실행될 때까지 대기
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 종료 중...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("✅ 종료됨")


def run_prod(auto_build=True):
    """프로덕션 모드 실행 (Waitress WSGI 서버).
    
    Args:
        auto_build: 자동 빌드 여부 (기본: True)
    """
    print("\n" + "=" * 70)
    print("🚀 Monitoring System - Production Mode")
    print("=" * 70)
    print()
    
    # 환경 변수 설정
    os.environ['PRODUCTION'] = 'True'
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    print("📝 환경 변수 설정:")
    print("  - PRODUCTION=True")
    print("  - FLASK_ENV=production")
    print("  - FLASK_DEBUG=False")
    print()
    
    # 프론트엔드 빌드 확인 및 자동 빌드
    dist_dir = PROJECT_ROOT / "dist"
    if auto_build or not dist_dir.exists():
        if not dist_dir.exists():
            print("⚠️ 프론트엔드 빌드 파일이 없습니다.")
        else:
            print("🔄 프론트엔드 재빌드 중...")
        
        print("📦 npm install 실행 중...")
        result = subprocess.run(
            ["npm.cmd", "install"],
            cwd=FRONTEND_DIR,
            capture_output=True,
            text=True,
            shell=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode != 0:
            print("❌ npm install 실패!")
            if result.stderr:
                print(result.stderr)
            return False
        print("✅ npm install 완료")
        
        print("🏗️ 프론트엔드 빌드 중...")
        result = subprocess.run(
            ["npm.cmd", "run", "build"],
            cwd=FRONTEND_DIR,
            shell=True
        )
        if result.returncode != 0:
            print("❌ 프론트엔드 빌드 실패!")
            return False
        print("✅ 프론트엔드 빌드 완료")
    else:
        print("✅ 프론트엔드 빌드 파일 확인됨 (재빌드 스킵)")
    print()
    
    # Waitress 서버 실행
    print("🔧 백엔드 시작 중...")
    print()
    
    # 백엔드 디렉토리를 Python 경로에 추가
    sys.path.insert(0, str(BACKEND_DIR))
    
    try:
        from waitress import serve
        from app import app
        from config import Config
        import multiprocessing
        
        # CPU 코어 수 기반 최적 스레드 수 계산
        CPU_COUNT = multiprocessing.cpu_count()
        OPTIMAL_THREADS = max(4, CPU_COUNT * 2)
        
        # 환경 변수에서 설정 읽기
        THREADS = int(os.getenv('WAITRESS_THREADS', OPTIMAL_THREADS))
        CHANNEL_TIMEOUT = int(os.getenv('WAITRESS_CHANNEL_TIMEOUT', '120'))
        CONNECTION_LIMIT = int(os.getenv('WAITRESS_CONNECTION_LIMIT', '100'))
        RECV_BYTES = int(os.getenv('WAITRESS_RECV_BYTES', '8192'))
        SEND_BYTES = int(os.getenv('WAITRESS_SEND_BYTES', '8192'))
        
        print("=" * 70)
        print("✅ 서버가 시작되었습니다")
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
        print()
        print("📍 접속 주소: http://localhost:8080")
        print("📊 시스템 리소스: http://localhost:8080/api/system/stats")
        print("📋 프로그램 목록: http://localhost:8080/api/programs")
        print()
        print("종료하려면: Ctrl + C")
        print()
        print("=" * 70)
        print()
        
        # Waitress 서버 실행
        serve(
            app,
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            threads=THREADS,
            connection_limit=CONNECTION_LIMIT,
            channel_timeout=CHANNEL_TIMEOUT,
            recv_bytes=RECV_BYTES,
            send_bytes=SEND_BYTES,
            cleanup_interval=30,
            asyncore_use_poll=True,
            url_scheme='http',
            _quiet=False,
            _profile=False,
            backlog=1024,
            ipv4=True,
            ipv6=False,
        )
    except KeyboardInterrupt:
        print("\n\n🛑 서버 종료됨")
    except Exception as e:
        print(f"\n\n❌ 서버 실행 오류: {str(e)}")


def run_deploy():
    """배포 자동화."""
    print("\n" + "=" * 70)
    print("📦 Monitoring System - Deploy")
    print("=" * 70)
    print()
    
    # 1. 프론트엔드 빌드
    print("[1/4] 프론트엔드 빌드 중...")
    result = subprocess.run(
        ["npm.cmd", "run", "build"],
        cwd=FRONTEND_DIR,
        shell=True
    )
    if result.returncode != 0:
        print("❌ 프론트엔드 빌드 실패!")
        return False
    print("✅ 프론트엔드 빌드 완료")
    print()
    
    # 2. 백엔드 의존성 설치
    print("[2/4] 백엔드 의존성 설치 중...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=BACKEND_DIR
    )
    if result.returncode != 0:
        print("❌ 의존성 설치 실패!")
        return False
    print("✅ 백엔드 의존성 설치 완료")
    print()
    
    # 3. 환경 변수 확인
    print("[3/4] 환경 변수 확인 중...")
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        print("⚠️  .env 파일이 없습니다!")
        print(".env.example을 .env로 복사 중...")
        example_file = PROJECT_ROOT / ".env.example"
        if example_file.exists():
            with open(example_file, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env 파일 생성됨 (기본값 사용)")
            print()
            print("⚠️  .env 파일을 확인하고 필요시 수정하세요:")
            print("  - SECRET_KEY 변경 권장")
            print("  - FLASK_PORT 확인")
            print("  - 기타 설정 확인")
        else:
            print("❌ .env.example 파일을 찾을 수 없습니다!")
            return False
    else:
        print("✅ .env 파일 확인됨")
    print()
    
    # 4. 배포 완료
    print("[4/4] 배포 준비 완료!")
    print()
    print("=" * 70)
    print("✅ 배포 완료")
    print("=" * 70)
    print()
    print("다음 명령으로 프로덕션 시작:")
    print("  python run.py --prod")
    print()
    print("또는 직접 실행:")
    print("  python serve.py")
    print()
    print("=" * 70)
    print()
    
    return True


def run_check_performance():
    """성능 확인."""
    print("\n" + "=" * 70)
    print("📊 Monitoring System - Performance Check")
    print("=" * 70)
    print()
    
    import psutil
    import platform
    
    # 1. 시스템 정보
    print("[1] 시스템 정보")
    print("-" * 70)
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print()
    
    # 2. CPU 정보
    print("[2] CPU 정보")
    print("-" * 70)
    print(f"코어 수: {psutil.cpu_count(logical=False)}")
    print(f"논리 프로세서: {psutil.cpu_count(logical=True)}")
    print()
    
    # 3. 메모리 정보
    print("[3] 메모리 사용량")
    print("-" * 70)
    memory = psutil.virtual_memory()
    print(f"총 메모리: {memory.total / (1024**3):.2f} GB")
    print(f"사용 중: {memory.used / (1024**3):.2f} GB")
    print(f"여유: {memory.available / (1024**3):.2f} GB")
    print(f"사용률: {memory.percent}%")
    print()
    
    # 4. 디스크 정보
    print("[4] 디스크 사용량")
    print("-" * 70)
    try:
        disk = psutil.disk_usage('C:\\')
        print(f"총 디스크: {disk.total / (1024**3):.2f} GB")
        print(f"사용 중: {disk.used / (1024**3):.2f} GB")
        print(f"여유: {disk.free / (1024**3):.2f} GB")
        print(f"사용률: {disk.percent}%")
    except Exception as e:
        print(f"디스크 정보 조회 실패: {e}")
    print()
    
    # 5. API 응답 시간
    print("[5] API 응답 시간")
    print("-" * 70)
    try:
        import requests
        import time
        
        start = time.time()
        response = requests.get('http://localhost:8080/api/programs', timeout=5)
        elapsed = (time.time() - start) * 1000
        
        print(f"응답 시간: {elapsed:.2f}ms")
        print(f"상태 코드: {response.status_code}")
    except Exception as e:
        print(f"API 연결 실패: {e}")
    print()
    
    # 6. 권장 설정
    print("[6] 권장 설정")
    print("-" * 70)
    print("권장 환경:")
    print("  - OS: Windows 10 이상")
    print("  - CPU: 2코어 이상")
    print("  - RAM: 4GB 이상")
    print("  - 디스크: 1GB 여유 공간")
    print()
    print("최적화 설정:")
    print("  - DB 연결 풀: 5개")
    print("  - 작업 큐 워커: 2개")
    print("  - 프로세스 모니터 간격: 3초")
    print("  - 메트릭 수집 간격: 1초")
    print()
    print("=" * 70)
    print()


def main():
    """메인 함수."""
    parser = argparse.ArgumentParser(
        description="모니터링 시스템 실행 스크립트"
    )
    parser.add_argument(
        '--dev',
        action='store_true',
        help='개발 모드 실행 (Flask + Vite)'
    )
    parser.add_argument(
        '--prod',
        action='store_true',
        help='프로덕션 모드 실행 (Waitress)'
    )
    parser.add_argument(
        '--deploy',
        action='store_true',
        help='배포 자동화'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='성능 확인'
    )
    parser.add_argument(
        '--no-build',
        action='store_true',
        help='프로덕션 모드에서 빌드 스킵 (빌드 파일이 이미 있는 경우)'
    )
    
    args = parser.parse_args()
    
    # 기본값: 프로덕션 모드 (자동 빌드 포함)
    if not any([args.dev, args.prod, args.deploy, args.check]):
        print("\n💡 기본 모드: 프로덕션 (빌드 → 배포)")
        print("   다른 모드: --dev (개발), --deploy (배포만), --check (성능 확인)")
        print()
        run_prod(auto_build=True)
    elif args.dev:
        run_dev()
    elif args.prod:
        # --no-build 플래그에 따라 빌드 여부 결정
        run_prod(auto_build=not args.no_build)
    elif args.deploy:
        if not run_deploy():
            sys.exit(1)
    elif args.check:
        run_check_performance()


if __name__ == '__main__':
    main()
