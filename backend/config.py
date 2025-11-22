"""애플리케이션 설정 및 경로 관리."""

import os
from pathlib import Path
from dotenv import load_dotenv

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent  # backend/
ROOT_DIR = BASE_DIR.parent  # monitoring/

# 루트 디렉토리의 .env 파일 로드
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
DATA_DIR.mkdir(exist_ok=True)

# JSON 파일 경로
USERS_JSON = DATA_DIR / "users.json"
PROGRAMS_JSON = DATA_DIR / "programs.json"
STATUS_JSON = DATA_DIR / "status.json"

# Flask 설정
class Config:
    """Flask 애플리케이션 설정 클래스."""
    
    # 환경 변수
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, production
    IS_PRODUCTION = ENVIRONMENT == "production"
    
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-monitoring-secret-key")
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    # 세션 설정
    PERMANENT_SESSION_LIFETIME = int(os.getenv("SESSION_LIFETIME", "3600"))  # 기본 1시간 (초 단위)
    SESSION_COOKIE_SECURE = IS_PRODUCTION  # 프로덕션에서만 HTTPS 전용
    SESSION_COOKIE_HTTPONLY = True  # JavaScript 접근 차단
    SESSION_COOKIE_SAMESITE = "Lax"  # CSRF 보호
    
    # CORS 설정 (환경별 분리)
    if IS_PRODUCTION:
        # 프로덕션: 특정 도메인만 허용
        CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")
    else:
        # 개발: 모든 origin 허용
        CORS_ORIGINS = "*"
