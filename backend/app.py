"""monitoring 프로젝트의 Flask 진입점.

Blueprint 기반 모듈화 구조:
- config.py: 애플리케이션 설정 및 경로
- routes/: 웹 페이지 라우트
- api/: REST API 엔드포인트
- utils/: 유틸리티 함수들
"""

# Windows 콘솔 UTF-8 인코딩 및 버퍼링 비활성화
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

from flask import Flask, send_from_directory, jsonify
from flask_compress import Compress
from config import Config, USERS_JSON, PROGRAMS_JSON, STATUS_JSON
from utils.data_manager import init_default_data
from utils.process_monitor import start_process_monitor, stop_process_monitor
from utils.auth import migrate_plain_passwords
from utils.data_manager import load_json, save_json
from datetime import timedelta
from pathlib import Path
import atexit
import os

# Flask 앱 생성 및 설정
app = Flask(__name__)
app.config.from_object(Config)

# 응답 압축 활성화 (gzip)
Compress(app)

# 게임 서버 환경: CPU 우선순위 낮추기
import psutil
try:
    current_process = psutil.Process()
    current_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    print("✅ [Game Server Mode] 모니터링 프로세스 우선순위 낮춤 (게임 서버 우선)")
except Exception as e:
    print(f"⚠️ [Game Server Mode] 우선순위 설정 실패: {str(e)}")

# Rate Limiter 초기화
from utils.rate_limiter import init_limiter
init_limiter(app)

# Prometheus 메트릭 초기화
from utils.prometheus_metrics import init_prometheus, prometheus_middleware
init_prometheus(app)
prometheus_middleware(app)

# SocketIO 제거 (REST API 폴링으로 대체)
# from utils.websocket import init_socketio
# socketio = init_socketio(app)

# 세션 타임아웃 설정
app.permanent_session_lifetime = timedelta(seconds=Config.PERMANENT_SESSION_LIFETIME)

# 앱 시작 시 기본 데이터 초기화
init_default_data(USERS_JSON, PROGRAMS_JSON, STATUS_JSON)

# 기존 평문 비밀번호를 해시로 마이그레이션
users_data = load_json(USERS_JSON, {"users": []})
users_data = migrate_plain_passwords(users_data)
save_json(USERS_JSON, users_data)

# SQLite 데이터베이스 초기화 및 마이그레이션
from utils.database import init_database, migrate_from_json, get_all_plugin_configs, DB_PATH
from utils.db_pool import init_pool
init_database()
migrate_from_json()

# DB 연결 풀 초기화 (5개 연결 - Windows PC 최적화)
init_pool(str(DB_PATH), pool_size=5)
print("[Database] DB 연결 풀 초기화 완료 (5개 연결)")

# 작업 큐 초기화 (2개 워커 - Windows PC 최적화)
from utils.job_queue import init_job_queue
init_job_queue(max_workers=2)
print("[JobQueue] 작업 큐 초기화 완료 (2개 워커)")

# PowerShell 에이전트 초기화
from utils.powershell_agent import init_powershell_agent
init_powershell_agent(max_queue_size=100)
print("[PowerShellAgent] PowerShell 에이전트 초기화 완료")

# 플러그인 시스템 초기화 및 저장된 플러그인 자동 로드
from plugins.loader import get_plugin_loader
loader = get_plugin_loader()  # 전역 싱글톤 인스턴스 사용

# 저장된 플러그인 설정 자동 로드
saved_plugins = get_all_plugin_configs()
if saved_plugins:
    print(f"[Plugin System] 저장된 플러그인 {len(saved_plugins)}개 로드 중...")
    for plugin_data in saved_plugins:
        program_id = plugin_data["program_id"]
        plugin_id = plugin_data["plugin_id"]
        config = plugin_data["config"]
        
        result = loader.load_plugin(program_id, plugin_id, config)
        if result:
            print(f"[Plugin System] ✅ {plugin_id} (프로그램 {program_id})")
        else:
            print(f"[Plugin System] ❌ {plugin_id} (프로그램 {program_id}) - 로드 실패")
else:
    print("[Plugin System] 저장된 플러그인 없음")

# 로그 로테이션 시작
from utils.log_rotation import get_log_rotation
log_rotation = get_log_rotation()
log_rotation.start()

# 프로세스 모니터 시작 (5초 간격 - 게임 서버 환경)
# 항상 실행 (DEBUG 모드에서도 모니터링 필요)
start_process_monitor(check_interval=5)

# 메트릭 버퍼 시작 (배치 쓰기 - 게임 서버 환경)
from utils.metric_buffer import get_metric_buffer, stop_metric_buffer
metric_buffer = get_metric_buffer()
print("✅ [Game Server Mode] 메트릭 버퍼링 시작 (디스크 I/O 최적화)")

# 메모리 관리자 초기화 (게임 서버 환경)
from utils.memory_manager import get_memory_manager
memory_manager = get_memory_manager()
print("✅ [Game Server Mode] 메모리 관리자 초기화")

# 앱 종료 시 전체 리소스 정리
def cleanup_all_resources():
    """모든 리소스 정리 (앱 종료 시)."""
    print("🧹 [Cleanup] 리소스 정리 시작")
    
    # 1. 메트릭 버퍼 플러시 및 중지
    try:
        stop_metric_buffer()
        print("✅ [Cleanup] 메트릭 버퍼 정리 완료")
    except Exception as e:
        print(f"⚠️ [Cleanup] 메트릭 버퍼 정리 실패: {e}")
    
    # 2. 프로세스 모니터 중지
    try:
        stop_process_monitor()
        print("✅ [Cleanup] 프로세스 모니터 정리 완료")
    except Exception as e:
        print(f"⚠️ [Cleanup] 프로세스 모니터 정리 실패: {e}")
    
    # 3. 데이터베이스 연결 풀 종료
    try:
        from utils.db_pool import get_pool
        pool = get_pool()
        pool.close_all()
        print("✅ [Cleanup] DB 연결 풀 정리 완료")
    except Exception as e:
        print(f"⚠️ [Cleanup] DB 풀 정리 실패: {e}")
    
    # 4. 웹훅 스레드 풀 종료
    try:
        from utils.webhook import shutdown_webhook_executor
        shutdown_webhook_executor()
        print("✅ [Cleanup] 웹훅 스레드 풀 정리 완료")
    except Exception as e:
        print(f"⚠️ [Cleanup] 웹훅 풀 정리 실패: {e}")
    
    print("✅ [Cleanup] 리소스 정리 완료")

atexit.register(cleanup_all_resources)

# === 에러 핸들러 등록 ===
from utils.exceptions import MonitoringError

@app.errorhandler(MonitoringError)
def handle_monitoring_error(error):
    """커스텀 예외 처리."""
    return jsonify(error.to_dict()), error.status_code

@app.errorhandler(404)
def handle_not_found(error):
    """404 Not Found 처리."""
    return jsonify({
        "success": False,
        "error": "요청한 리소스를 찾을 수 없습니다",
        "error_code": "NOT_FOUND"
    }), 404

@app.errorhandler(500)
def handle_internal_error(error):
    """500 Internal Server Error 처리."""
    return jsonify({
        "success": False,
        "error": "서버 내부 오류가 발생했습니다",
        "error_code": "INTERNAL_SERVER_ERROR"
    }), 500

# === 프론트엔드 빌드 파일 서빙 (프로덕션 모드) ===
# 프론트엔드 빌드 디렉토리 경로 (루트의 dist 폴더)
FRONTEND_DIST = Path(__file__).parent.parent / "dist"

if FRONTEND_DIST.exists() and os.getenv("PRODUCTION", "False").lower() == "true":
    print(f"[Production Mode] 프론트엔드 빌드 파일 서빙: {FRONTEND_DIST}")
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """프론트엔드 빌드 파일 서빙 (SPA 라우팅 지원)."""
        # API 요청은 제외
        if path.startswith('api/'):
            return {"error": "Not Found"}, 404
        
        # Blueprint 라우트는 제외 (login, logout 등)
        if path in ['login', 'logout']:
            return {"error": "Not Found"}, 404
        
        # 파일이 존재하면 해당 파일 반환
        if path and (FRONTEND_DIST / path).exists():
            return send_from_directory(FRONTEND_DIST, path)
        
        # 그 외에는 index.html 반환 (SPA 라우팅)
        return send_from_directory(FRONTEND_DIST, 'index.html')
else:
    print("[Development Mode] 프론트엔드는 별도 개발 서버(Vite)에서 실행됩니다")

# === 성능 모니터링 API 등록 ===
from utils.performance_monitor import create_performance_api
create_performance_api(app)

# === Blueprint 등록 ===

# 웹 페이지 라우트 등록
from routes.web import web_bp
app.register_blueprint(web_bp)

# API 엔드포인트 등록
from api.programs import programs_api
from api.status import status_api
from api.webhook import webhook_api
from api.file_explorer import file_explorer_api
from api.jobs import jobs_api
from api.powershell import powershell_api
from api.metrics import metrics_api
from api.plugins import plugins_api
from api.system import system_api
from api.cache_stats import cache_stats_api
from api.health import health_api
app.register_blueprint(programs_api)
app.register_blueprint(status_api)
app.register_blueprint(webhook_api)
app.register_blueprint(file_explorer_api)
app.register_blueprint(jobs_api)
app.register_blueprint(powershell_api)
app.register_blueprint(metrics_api)
app.register_blueprint(plugins_api)
app.register_blueprint(system_api)
app.register_blueprint(cache_stats_api)
app.register_blueprint(health_api)


if __name__ == "__main__":
    # Config에서 설정 읽기
    # 개발 모드에서는 Flask 내장 서버 사용
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
        use_reloader=False  # 자동 재시작 비활성화
    )
