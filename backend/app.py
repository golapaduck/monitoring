"""monitoring 프로젝트의 Flask 진입점.

Blueprint 기반 모듈화 구조:
- config.py: 애플리케이션 설정 및 경로
- routes/: 웹 페이지 라우트
- api/: REST API 엔드포인트
- utils/: 유틸리티 함수들
"""

# Windows 콘솔 UTF-8 인코딩 설정
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask
from config import Config, USERS_JSON, PROGRAMS_JSON, STATUS_JSON
from utils.data_manager import init_default_data
from utils.process_monitor import start_process_monitor, stop_process_monitor
from utils.auth import migrate_plain_passwords
from utils.data_manager import load_json, save_json
from datetime import timedelta
import atexit
import os

# Flask 앱 생성 및 설정
app = Flask(__name__)
app.config.from_object(Config)

# 세션 타임아웃 설정
app.permanent_session_lifetime = timedelta(seconds=Config.PERMANENT_SESSION_LIFETIME)

# 앱 시작 시 기본 데이터 초기화
init_default_data(USERS_JSON, PROGRAMS_JSON, STATUS_JSON)

# 기존 평문 비밀번호를 해시로 마이그레이션
users_data = load_json(USERS_JSON, {"users": []})
users_data = migrate_plain_passwords(users_data)
save_json(USERS_JSON, users_data)

# SQLite 데이터베이스 초기화 및 마이그레이션
from utils.database import init_database, migrate_from_json
init_database()
migrate_from_json()

# 프로세스 모니터 시작 (10초 간격)
# 항상 실행 (DEBUG 모드에서도 모니터링 필요)
start_process_monitor(check_interval=10)
# 앱 종료 시 모니터 중지
atexit.register(stop_process_monitor)

# === Blueprint 등록 ===

# 웹 페이지 라우트 등록
from routes.web import web_bp
app.register_blueprint(web_bp)

# API 엔드포인트 등록
from api.programs import programs_api
from api.status import status_api
from api.webhook import webhook_api
from api.file_explorer import file_explorer_api
from api.metrics import metrics_api
app.register_blueprint(programs_api)
app.register_blueprint(status_api)
app.register_blueprint(webhook_api)
app.register_blueprint(file_explorer_api)
app.register_blueprint(metrics_api)


if __name__ == "__main__":
    # Config에서 설정 읽기
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
        use_reloader=False  # 자동 재시작 비활성화
    )
