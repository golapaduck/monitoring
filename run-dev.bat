@echo off
chcp 65001 > nul
echo ========================================
echo   Monitoring 프로젝트 (개발 모드)
echo ========================================
echo.

:: .env 파일 확인
if not exist ".env" (
    echo ❌ .env 파일이 없습니다.
    echo.
    echo .env.example을 복사하여 .env 파일을 생성하세요:
    echo   copy .env.example .env
    echo.
    pause
    exit /b 1
)

:: .env 파일에서 PRODUCTION=True를 PRODUCTION=False로 변경
echo [설정] 개발 모드 활성화 중...
powershell -Command "(Get-Content .env) -replace 'PRODUCTION=True', 'PRODUCTION=False' | Set-Content .env"
echo ✅ 개발 모드 활성화
echo.

:: 서버 정보 출력
echo ========================================
echo   개발 모드로 실행합니다
echo ========================================
echo.
echo 🔧 백엔드 서버: http://localhost:8080
echo 🎨 프론트엔드 서버: http://localhost:5173 (별도 실행 필요)
echo.
echo 프론트엔드 개발 서버 실행:
echo   cd frontend
echo   npm run dev
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요
echo ========================================
echo.

:: Python 서버 실행
cd backend
python -u app.py
