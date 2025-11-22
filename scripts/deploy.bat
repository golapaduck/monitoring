@echo off
REM ============================================
REM 배포 자동화 스크립트
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Monitoring System - Deploy Script
echo ========================================
echo.

REM 프로젝트 루트 디렉토리로 이동
cd /d "%~dp0.."

REM 1. 프론트엔드 빌드
echo [1/4] 프론트엔드 빌드 중...
cd frontend
call npm run build
if errorlevel 1 (
    echo ❌ 프론트엔드 빌드 실패!
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✅ 프론트엔드 빌드 완료
echo.

REM 2. 백엔드 의존성 설치
echo [2/4] 백엔드 의존성 설치 중...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 의존성 설치 실패!
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✅ 백엔드 의존성 설치 완료
echo.

REM 3. 환경 변수 확인
echo [3/4] 환경 변수 확인 중...
if not exist ".env" (
    echo ⚠️  .env 파일이 없습니다!
    echo .env.example을 .env로 복사 중...
    copy .env.example .env
    echo ✅ .env 파일 생성됨 (기본값 사용)
    echo.
    echo ⚠️  .env 파일을 확인하고 필요시 수정하세요:
    echo - SECRET_KEY 변경 권장
    echo - FLASK_PORT 확인
    echo - 기타 설정 확인
    echo.
) else (
    echo ✅ .env 파일 확인됨
)
echo.

REM 4. 배포 완료
echo [4/4] 배포 준비 완료!
echo.
echo ========================================
echo  배포 완료
echo ========================================
echo.
echo 다음 명령으로 프로덕션 시작:
echo   scripts\prod.bat
echo.
echo 또는 직접 실행:
echo   python serve.py
echo.
echo ========================================
echo.

pause
