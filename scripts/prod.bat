@echo off
chcp 65001 > nul

:: 매개변수 확인 (build = 빌드만, run = 실행만, 없으면 빌드+실행)
set MODE=%1
if "%MODE%"=="" set MODE=deploy

echo ========================================
echo   Monitoring 프로젝트 (프로덕션 모드)
echo ========================================
echo.

:: 모드에 따라 실행
if /i "%MODE%"=="build" goto BUILD_ONLY
if /i "%MODE%"=="run" goto RUN_ONLY
if /i "%MODE%"=="deploy" goto DEPLOY

:BUILD_ONLY
echo [빌드] 프론트엔드 빌드 중...
cd frontend
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 프론트엔드 빌드 실패
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✅ 프론트엔드 빌드 완료
echo.
pause
goto END

:RUN_ONLY
:: 빌드 파일 확인
if not exist "frontend\dist\index.html" (
    echo ❌ 프론트엔드 빌드 파일이 없습니다.
    echo.
    echo 먼저 빌드를 실행하세요:
    echo   scripts\prod.bat build
    echo.
    pause
    exit /b 1
)

:: .env 파일 백업 및 프로덕션 모드 설정
echo [설정] 프로덕션 모드 활성화 중...
if exist ".env" (
    if not exist ".env.backup" (
        copy ".env" ".env.backup" > nul
    )
)

powershell -Command "(Get-Content .env) -replace 'PRODUCTION=False', 'PRODUCTION=True' | Set-Content .env"
echo ✅ 프로덕션 모드 활성화
echo.

echo ========================================
echo   프로덕션 모드로 실행합니다
echo ========================================
echo.
echo 📦 백엔드 + 프론트엔드 통합 서버
echo 🌐 URL: http://localhost:8080
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요
echo ========================================
echo.

:: Python 서버 실행
cd backend
python -u app.py

:: 서버 종료 후 .env 복원
cd ..
echo.
echo [정리] .env 파일 복원 중...
if exist ".env.backup" (
    copy ".env.backup" ".env" > nul
    del ".env.backup"
    echo ✅ .env 파일 복원 완료
)
goto END

:DEPLOY
echo [1/2] 프론트엔드 빌드 중...
cd frontend
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 프론트엔드 빌드 실패
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✅ 프론트엔드 빌드 완료
echo.

:: .env 파일 백업 및 프로덕션 모드 설정
echo [2/2] 프로덕션 모드 설정 중...
if exist ".env" (
    if not exist ".env.backup" (
        copy ".env" ".env.backup" > nul
    )
)

powershell -Command "(Get-Content .env) -replace 'PRODUCTION=False', 'PRODUCTION=True' | Set-Content .env"
echo ✅ 프로덕션 모드 활성화
echo.

echo ========================================
echo   배포 완료!
echo ========================================
echo.
echo 📦 백엔드 + 프론트엔드 통합 서버
echo 🌐 URL: http://localhost:8080
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요
echo ========================================
echo.

:: Python 서버 실행
cd backend
python -u app.py

:: 서버 종료 후 .env 복원
cd ..
echo.
echo [정리] .env 파일 복원 중...
if exist ".env.backup" (
    copy ".env.backup" ".env" > nul
    del ".env.backup"
    echo ✅ .env 파일 복원 완료
)
goto END

:END
