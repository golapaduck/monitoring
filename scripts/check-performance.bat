@echo off
REM ============================================
REM 성능 확인 스크립트 (Windows PC 최적화)
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Monitoring System - 성능 확인
echo ========================================
echo.

REM 1. 시스템 정보 확인
echo [1] 시스템 정보
echo ----------------------------------------
wmic os get name,totalvisiblememorysize,freephysicalmemory | findstr /v "^$"
echo.

REM 2. CPU 정보
echo [2] CPU 정보
echo ----------------------------------------
wmic cpu get name,numberofcores,numberoflogicalprocessors | findstr /v "^$"
echo.

REM 3. 메모리 사용량
echo [3] 메모리 사용량
echo ----------------------------------------
for /f "tokens=2" %%A in ('wmic os get totalvisiblememorysize ^| findstr [0-9]') do set total=%%A
for /f "tokens=2" %%A in ('wmic os get freephysicalmemory ^| findstr [0-9]') do set free=%%A

setlocal enabledelayedexpansion
set /a used=!total! - !free!
set /a percent=!used! * 100 / !total!

echo 총 메모리: !total! KB
echo 사용 중: !used! KB
echo 여유: !free! KB
echo 사용률: !percent!%%
echo.

REM 4. Python 프로세스 확인
echo [4] Python 프로세스 확인
echo ----------------------------------------
tasklist | findstr python
if errorlevel 1 (
    echo Python 프로세스 없음
) else (
    echo Python 프로세스 실행 중
)
echo.

REM 5. 포트 확인
echo [5] 포트 확인
echo ----------------------------------------
echo Flask 백엔드 (포트 8080):
netstat -ano | findstr :8080
if errorlevel 1 (
    echo 포트 8080 미사용
) else (
    echo 포트 8080 사용 중
)
echo.

REM 6. 응답 시간 측정
echo [6] API 응답 시간 측정
echo ----------------------------------------
echo http://localhost:8080/api/programs 응답 시간:
powershell -Command "
try {
    $start = Get-Date
    $response = Invoke-WebRequest -Uri 'http://localhost:8080/api/programs' -TimeoutSec 5 -ErrorAction Stop
    $end = Get-Date
    $time = ($end - $start).TotalMilliseconds
    Write-Host \"응답 시간: $([Math]::Round($time, 2))ms\"
    Write-Host \"상태 코드: $($response.StatusCode)\"
} catch {
    Write-Host \"연결 실패: $_\"
}
"
echo.

REM 7. 권장 설정 확인
echo [7] 권장 설정 확인
echo ----------------------------------------
echo 권장 환경:
echo - OS: Windows 10 이상
echo - CPU: 2코어 이상
echo - RAM: 4GB 이상
echo - 디스크: 1GB 여유 공간
echo.
echo 최적화 설정:
echo - DB 연결 풀: 5개
echo - 작업 큐 워커: 2개
echo - 프로세스 모니터 간격: 3초
echo - 메트릭 수집 간격: 1초
echo.

echo ========================================
echo  성능 확인 완료
echo ========================================
echo.

pause
