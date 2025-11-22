@echo off
chcp 65001 > nul
echo ========================================
echo   Monitoring 프로젝트 빌드
echo ========================================
echo.

:: 프론트엔드 빌드
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

:: 빌드 완료 메시지
echo ========================================
echo   빌드 완료!
echo ========================================
echo.
echo 프로덕션 모드로 실행하려면:
echo   run-production.bat
echo.
pause
