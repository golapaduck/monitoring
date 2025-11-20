# Monitoring 시스템 시작 스크립트
# Windows 작업 스케줄러에서 실행하기 위한 PowerShell 스크립트

# 스크립트 위치 기준으로 프로젝트 루트 경로 설정
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# 로그 디렉토리 생성
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# 로그 파일 경로
$LogFile = Join-Path $LogDir "monitoring_$(Get-Date -Format 'yyyyMMdd').log"

# 로그 함수
function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Add-Content -Path $LogFile -Value $LogMessage
    Write-Host $LogMessage
}

Write-Log "=== Monitoring 시스템 시작 ==="

# Python 경로 확인
$PythonCmd = "python"
try {
    $PythonVersion = & $PythonCmd --version 2>&1
    Write-Log "Python 버전: $PythonVersion"
} catch {
    Write-Log "ERROR: Python을 찾을 수 없습니다. Python이 설치되어 있고 PATH에 등록되어 있는지 확인하세요."
    exit 1
}

# 프로젝트 디렉토리로 이동
Set-Location $ProjectRoot
Write-Log "작업 디렉토리: $ProjectRoot"

# 가상환경 확인 (선택사항)
$VenvPath = Join-Path $ProjectRoot ".venv"
if (Test-Path $VenvPath) {
    Write-Log "가상환경 활성화: $VenvPath"
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        & $ActivateScript
    }
}

# Flask 앱이 이미 실행 중인지 확인
$ExistingProcess = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*app.py*"
}

if ($ExistingProcess) {
    Write-Log "WARNING: Flask 앱이 이미 실행 중입니다 (PID: $($ExistingProcess.Id))"
    Write-Log "기존 프로세스를 종료하고 재시작합니다..."
    Stop-Process -Id $ExistingProcess.Id -Force
    Start-Sleep -Seconds 2
}

# Flask 앱 실행
Write-Log "Flask 앱 시작..."
try {
    # 백그라운드에서 실행
    $Process = Start-Process -FilePath $PythonCmd `
                             -ArgumentList "app.py" `
                             -WorkingDirectory $ProjectRoot `
                             -WindowStyle Hidden `
                             -PassThru
    
    Write-Log "Flask 앱이 시작되었습니다 (PID: $($Process.Id))"
    
    # 프로세스가 정상적으로 시작되었는지 확인
    Start-Sleep -Seconds 3
    if ($Process.HasExited) {
        Write-Log "ERROR: Flask 앱이 시작 직후 종료되었습니다. 로그를 확인하세요."
        exit 1
    } else {
        Write-Log "Flask 앱이 정상적으로 실행 중입니다."
    }
    
} catch {
    Write-Log "ERROR: Flask 앱 시작 실패 - $_"
    exit 1
}

Write-Log "=== Monitoring 시스템 시작 완료 ==="
