@echo off
REM 테스트 실행 스크립트

echo ========================================
echo 테스트 실행 중...
echo ========================================
echo.

cd /d "%~dp0..\backend"

REM 가상환경 활성화 (존재하는 경우)
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM pytest 실행
echo [1/3] 전체 테스트 실행...
python -m pytest

echo.
echo [2/3] 커버리지 리포트 생성...
python -m pytest --cov-report=html

echo.
echo [3/3] 특정 테스트만 실행하려면:
echo   python -m pytest tests/test_structured_logger.py
echo   python -m pytest tests/test_error_handler.py
echo   python -m pytest tests/test_database.py
echo   python -m pytest -m unit
echo   python -m pytest -m "not slow"

echo.
echo ========================================
echo 테스트 완료!
echo 커버리지 리포트: backend\htmlcov\index.html
echo ========================================

pause
