"""monitoring 프로젝트의 Flask 진입점.

Blueprint 기반 모듈화 구조:
- config.py: 애플리케이션 설정 및 경로
- routes/: 웹 페이지 라우트
- api/: REST API 엔드포인트
- utils/: 유틸리티 함수들
"""

from flask import Flask
from config import Config, USERS_JSON, PROGRAMS_JSON, STATUS_JSON
from utils.data_manager import init_default_data

# Flask 앱 생성 및 설정
app = Flask(__name__)
app.config.from_object(Config)


# 앱 시작 시 기본 데이터 초기화
init_default_data(USERS_JSON, PROGRAMS_JSON, STATUS_JSON)


# === Blueprint 등록 ===

# 웹 페이지 라우트 등록
from routes.web import web_bp
app.register_blueprint(web_bp)

# API 엔드포인트 등록
from api.programs import programs_api
from api.status import status_api
from api.webhook import webhook_api
app.register_blueprint(programs_api)
app.register_blueprint(status_api)
app.register_blueprint(webhook_api)


if __name__ == "__main__":
    # Config에서 설정 읽기
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
