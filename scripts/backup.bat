@echo off
REM 백업 스크립트 (Windows)

REM 설정
set BACKUP_DIR=C:\Backups\monitoring
set SOURCE_DIR=%~dp0..\data
set DATE_TIME=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set DATE_TIME=%DATE_TIME: =0%

REM 백업 디렉토리 생성
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 백업 파일명
set BACKUP_FILE=%BACKUP_DIR%\monitoring_backup_%DATE_TIME%.zip

REM 백업 생성 (PowerShell 사용)
echo 백업 생성 중: %BACKUP_FILE%
powershell -Command "Compress-Archive -Path '%SOURCE_DIR%' -DestinationPath '%BACKUP_FILE%' -Force"

if %ERRORLEVEL% EQU 0 (
    echo ✅ 백업 완료: %BACKUP_FILE%
) else (
    echo ❌ 백업 실패
    exit /b 1
)

REM 7일 이상 된 백업 삭제
echo 오래된 백업 파일 정리 중...
forfiles /P "%BACKUP_DIR%" /M monitoring_backup_*.zip /D -7 /C "cmd /c del @path" 2>nul

echo ✅ 백업 작업 완료
