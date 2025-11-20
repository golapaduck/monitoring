# 🚀 프로덕션 배포 가이드 (Windows)

## 📋 목차
1. [환경 설정](#1-환경-설정)
2. [Waitress 설치 및 실행](#2-waitress-설치-및-실행)
3. [Windows 서비스 등록](#3-windows-서비스-등록)
4. [헬스체크 및 모니터링](#4-헬스체크-및-모니터링)
5. [백업 설정](#5-백업-설정)

---

## 1. 환경 설정

### `.env` 파일 생성
프로젝트 루트에 `.env` 파일을 생성하세요:

```env
SECRET_KEY=your-super-secret-key-here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
DATA_DIR=data
```

### 보안 키 생성
PowerShell에서 실행:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

생성된 키를 `.env` 파일의 `SECRET_KEY`에 복사하세요.

---

## 2. Waitress 설치 및 실행

### 1️⃣ Waitress 설치
```bash
pip install -r requirements.txt
```

### 2️⃣ 프로덕션 서버 실행
```bash
python serve.py
```

### 3️⃣ 서버 확인
브라우저에서 접속:
- http://localhost:5000
- http://127.0.0.1:5000

헬스체크:
- http://localhost:5000/health

---

## 3. Windows 서비스 등록

### Option 1: NSSM (권장)

#### 1. NSSM 다운로드
https://nssm.cc/download 에서 다운로드

#### 2. NSSM 압축 해제
`C:\Tools\nssm` 에 압축 해제

#### 3. 환경 변수 PATH 추가
시스템 환경 변수에 `C:\Tools\nssm\win64` 추가

#### 4. 서비스 설치
PowerShell (관리자 권한):
```powershell
# Python 경로 확인
where python

# 서비스 설치
nssm install Monitoring "C:\Python313\python.exe" "C:\Programming\CascadeProjects\monitoring\serve.py"

# 작업 디렉토리 설정
nssm set Monitoring AppDirectory "C:\Programming\CascadeProjects\monitoring"

# 서비스 표시 이름
nssm set Monitoring DisplayName "Program Monitoring System"

# 서비스 설명
nssm set Monitoring Description "프로그램 모니터링 및 Discord 알림 시스템"

# 자동 시작 설정
nssm set Monitoring Start SERVICE_AUTO_START

# 로그 파일 설정
nssm set Monitoring AppStdout "C:\Programming\CascadeProjects\monitoring\logs\service.log"
nssm set Monitoring AppStderr "C:\Programming\CascadeProjects\monitoring\logs\service_error.log"
```

#### 5. 서비스 관리
```powershell
# 서비스 시작
nssm start Monitoring

# 서비스 중지
nssm stop Monitoring

# 서비스 재시작
nssm restart Monitoring

# 서비스 상태 확인
nssm status Monitoring

# 서비스 제거
nssm remove Monitoring confirm
```

#### 6. Windows 서비스 관리자에서 확인
```
Win + R → services.msc → "Program Monitoring System" 찾기
```

---

### Option 2: Task Scheduler (대안)

#### 1. 작업 스케줄러 열기
```
Win + R → taskschd.msc
```

#### 2. 새 작업 만들기
- **일반 탭**
  - 이름: `Monitoring System`
  - 설명: `프로그램 모니터링 시스템`
  - 사용자 계정: `SYSTEM`
  - 가장 높은 수준의 권한으로 실행: ✅

- **트리거 탭**
  - 새로 만들기 → 시작: `시스템 시작 시`
  - 지연: `1분`

- **동작 탭**
  - 새로 만들기 → 프로그램/스크립트: `C:\Python313\python.exe`
  - 인수 추가: `serve.py`
  - 시작 위치: `C:\Programming\CascadeProjects\monitoring`

- **조건 탭**
  - 전원: 모두 해제

- **설정 탭**
  - 작업이 실패하면 다시 시작: ✅
  - 다시 시작 간격: `1분`

---

## 4. 헬스체크 및 모니터링

### 헬스체크 엔드포인트
```
GET http://localhost:5000/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "timestamp": 1700000000.0,
  "service": "monitoring"
}
```

### 외부 모니터링 서비스

#### 1. UptimeRobot (무료)
https://uptimerobot.com

- Monitor Type: HTTP(s)
- URL: `http://your-server:5000/health`
- Monitoring Interval: 5분

#### 2. StatusCake (무료)
https://www.statuscake.com

- Test Type: Uptime
- Website URL: `http://your-server:5000/health`
- Check Rate: 5분

---

## 5. 백업 설정

### 자동 백업 스크립트

#### 1. 백업 스크립트 실행
```bash
scripts\backup.bat
```

#### 2. 작업 스케줄러로 자동화

**작업 스케줄러 열기:**
```
Win + R → taskschd.msc
```

**새 작업 만들기:**
- **일반 탭**
  - 이름: `Monitoring Backup`
  - 설명: `데이터 자동 백업`

- **트리거 탭**
  - 새로 만들기 → 일정: `매일`
  - 시작 시간: `03:00:00` (새벽 3시)

- **동작 탭**
  - 새로 만들기 → 프로그램/스크립트: `C:\Programming\CascadeProjects\monitoring\scripts\backup.bat`

- **조건 탭**
  - 전원: 모두 해제

**백업 위치:**
```
C:\Backups\monitoring\
```

**백업 파일 형식:**
```
monitoring_backup_20251120_030000.zip
```

**자동 정리:**
- 7일 이상 된 백업 파일 자동 삭제

---

## 6. 로그 관리

### 로그 파일 위치
```
logs/
├── service.log          # 서비스 표준 출력
├── service_error.log    # 서비스 에러 출력
├── access.log           # 접근 로그 (선택)
└── error.log            # 에러 로그 (선택)
```

### 로그 확인
```powershell
# 실시간 로그 확인 (PowerShell)
Get-Content -Path "logs\service.log" -Wait -Tail 50
```

### 로그 정리
로그 파일이 너무 커지면 수동으로 정리하거나, 작업 스케줄러로 자동화:

```powershell
# 30일 이상 된 로그 삭제
Get-ChildItem -Path "logs" -Filter "*.log" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item
```

---

## 7. 방화벽 설정

### Windows 방화벽 규칙 추가

PowerShell (관리자 권한):
```powershell
# 인바운드 규칙 추가
New-NetFirewallRule -DisplayName "Monitoring System" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

또는 GUI:
```
제어판 → Windows Defender 방화벽 → 고급 설정 → 인바운드 규칙 → 새 규칙
→ 포트 → TCP → 특정 로컬 포트: 5000 → 연결 허용
```

---

## 8. 성능 최적화

### Waitress 설정 조정

`serve.py`에서 스레드 수 조정:
```python
serve(
    app,
    host='0.0.0.0',
    port=5000,
    threads=8,  # CPU 코어 수에 맞게 조정
    ...
)
```

**권장 스레드 수:**
- 2코어: 4 threads
- 4코어: 8 threads
- 8코어: 16 threads

---

## 9. 보안 체크리스트

프로덕션 배포 전 확인:

- [ ] `.env` 파일에 강력한 SECRET_KEY 설정
- [ ] `FLASK_DEBUG=False` 설정 확인
- [ ] 기본 관리자 비밀번호 변경
- [ ] 방화벽 규칙 설정
- [ ] 백업 스크립트 테스트
- [ ] 헬스체크 엔드포인트 확인
- [ ] 서비스 자동 시작 설정
- [ ] 로그 파일 권한 확인

---

## 10. 문제 해결

### 서비스가 시작되지 않는 경우

1. **로그 확인**
   ```
   logs\service_error.log
   ```

2. **Python 경로 확인**
   ```powershell
   where python
   ```

3. **수동 실행 테스트**
   ```bash
   python serve.py
   ```

### 포트가 이미 사용 중인 경우

```powershell
# 포트 사용 프로세스 확인
netstat -ano | findstr :5000

# 프로세스 종료
taskkill /PID <PID> /F
```

### 웹훅이 전송되지 않는 경우

1. **웹훅 설정 확인**
   - 대시보드 → ⚙️ 설정 → 웹훅 활성화
   - crash 이벤트 체크 확인

2. **프로그램별 웹훅 URL 확인**
   - 프로그램 편집 → 웹훅 URL 입력

3. **로그 확인**
   ```
   🚀 [Webhook] 비동기 전송 시작
   ✅ [Webhook] 알림 전송 성공
   ```

---

## 📞 지원

문제가 발생하면:
1. `logs/service_error.log` 확인
2. GitHub Issues: https://github.com/golapaduck/monitoring/issues
3. 헬스체크 엔드포인트 확인: http://localhost:5000/health

---

## 🎯 프로덕션 배포 완료!

모든 설정이 완료되면:
1. ✅ 서비스가 자동으로 시작됩니다
2. ✅ 매일 새벽 3시에 자동 백업됩니다
3. ✅ 프로세스 크래시를 자동으로 감지합니다
4. ✅ Discord로 실시간 알림을 받습니다

성공적인 배포를 기원합니다! 🚀
