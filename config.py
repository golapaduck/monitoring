"""애플리케이션 설정 및 경로 관리."""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
DATA_DIR.mkdir(exist_ok=True)

# JSON 파일 경로
USERS_JSON = DATA_DIR / "users.json"
PROGRAMS_JSON = DATA_DIR / "programs.json"
STATUS_JSON = DATA_DIR / "status.json"

# Flask 설정
class Config:
    """Flask 애플리케이션 설정 클래스."""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-monitoring-secret-key")
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
