# Monitoring System

Windows 서버에서 실행되는 프로그램들을 관제하고 관리하는 경량 모니터링 시스템입니다.

## 주요 기능

### 관리자 계정
- 프로그램 등록/삭제
- 프로그램 실행/종료
- 프로그램 상태 조회

### 게스트 계정
- 프로그램 상태 조회
- 프로그램 재부팅

## 기술 스택

- **백엔드**: Flask (Python)
- **프론트엔드**: HTML, CSS, JavaScript + Bootstrap 5
- **데이터 저장**: JSON 파일
- **운영**: Windows 작업 스케줄러

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 수정하세요:

```bash
copy .env.example .env
```

주요 설정:

**백엔드 (Flask):**
- `FLASK_HOST`: Flask 서버 호스트 (기본: 0.0.0.0)
- `FLASK_PORT`: Flask 서버 포트 (기본: 8080)
- `FLASK_DEBUG`: 디버그 모드 (개발: True, 운영: False)
- `SECRET_KEY`: 세션 암호화 키 (운영 환경에서는 반드시 변경!)

**프론트엔드 (Vite):**
- `VITE_PORT`: Vite 개발 서버 포트 (기본: 5173)
- `VITE_BACKEND_URL`: 백엔드 API URL (기본: http://localhost:8080)

### 3. 개발 모드 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 접속

### 4. 24시간 자동 실행 (Windows 작업 스케줄러)

자세한 내용은 [Windows 작업 스케줄러 설정 가이드](doc/windows-task-scheduler-guide.md)를 참고하세요.

간단 요약:
1. PowerShell 스크립트 실행 권한 설정
2. 작업 스케줄러에서 `scripts/start_monitoring.ps1` 등록
3. 시스템 부팅 시 자동 실행 설정

### 5. 기본 계정

- **관리자**: `admin` / `admin`
- **게스트**: `guest` / `guest`

⚠️ **보안 주의**: 실서비스 배포 전 반드시 비밀번호를 변경하세요!

## 프로젝트 구조

```
windsurf-project/
├── app.py                    # Flask 애플리케이션 진입점 (43줄)
├── config.py                 # 설정 및 경로 관리
├── requirements.txt          # Python 의존성
├── README.md                # 프로젝트 문서
├── .env                     # 환경 변수 (gitignore)
├── .env.example             # 환경 변수 템플릿
├── routes/                  # 웹 페이지 라우트
│   ├── __init__.py
│   └── web.py              # 로그인, 대시보드 등
├── api/                     # REST API 엔드포인트
│   ├── __init__.py
│   ├── programs.py         # 프로그램 제어 API
│   └── status.py           # 상태 조회 API
├── utils/                   # 유틸리티 함수
│   ├── __init__.py
│   ├── data_manager.py     # JSON 파일 처리
│   └── process_manager.py  # 프로세스 관리
├── templates/               # HTML 템플릿
│   ├── login.html          # 로그인 페이지
│   └── dashboard.html      # 대시보드
├── scripts/                 # 운영 스크립트
│   └── start_monitoring.ps1 # 자동 시작 스크립트
├── doc/                     # 개발 문서
│   ├── development-progress.md
│   └── windows-task-scheduler-guide.md
├── data/                    # JSON 데이터 저장소 (자동 생성)
│   ├── users.json          # 사용자 정보
│   ├── programs.json       # 프로그램 목록
│   └── status.json         # 프로그램 상태
└── logs/                    # 로그 파일 (자동 생성)
    └── monitoring_YYYYMMDD.log
```

## 다음 단계

1. PowerShell 에이전트 스크립트 작성 (프로그램 상태 수집)
2. Windows 작업 스케줄러 설정 가이드 작성
3. 프로그램 실행/종료 제어 기능 구현
4. 자동 재시작 로직 구현

## 보안 주의사항

- 현재 비밀번호는 평문으로 저장됩니다 (프로토타입 단계)
- 실서비스 배포 시 반드시 비밀번호 해싱 적용 필요
- SECRET_KEY를 환경변수로 분리 필요
