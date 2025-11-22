# Monitoring System

Windows 서버에서 실행되는 프로그램들을 관제하고 관리하는 모니터링 시스템입니다.

## 주요 기능

### 🎯 프로그램 관리
- **프로그램 등록/수정/삭제** (관리자)
- **프로그램 실행/종료/재시작** (관리자/게스트)
- **강제 종료** (자식 프로세스까지 완전 정리)
- **실시간 상태 모니터링** (5초 간격)
- **프로그램별 상세 대시보드**

### 📊 리소스 모니터링
- **CPU/메모리 사용량 실시간 추적**
- **리소스 사용 히스토리 차트** (시간대별)
- **프로세스 정보** (PID, 가동 시간)
- **웹소켓 실시간 업데이트** (상태 변경 즉시 반영)

### 🔍 고급 모니터링
- **프로세스 감지 더블 체크** (PID + 프로세스 이름 검증)
- **배치 처리 최적화** (프로세스 상태 일괄 조회로 30-50% 성능 향상)
- **로그 로테이션** (자동 백업 및 압축)
- **실시간 알림** (웹소켓 기반)

### 🔔 알림 시스템
- **웹훅 알림** (Discord, Slack 등)
- **프로그램별 웹훅 설정**
- **비정상 종료 감지 및 알림**

### 🧩 플러그인 시스템
- **RCON Controller**: 게임 서버 원격 제어 (Minecraft, Palworld 등)
- **Palworld REST API**: Palworld 서버 전용 REST API 제어
- **REST API Controller**: 범용 HTTP API 호출 및 웹훅 전송
- **플러그인 동적 로딩**
- **프로그램별 플러그인 설정**

### 🎮 게임 서버 조작
- **조작 탭**: 게임 서버 전용 빠른 액션 실행
- **플레이어 관리**: 강퇴, 차단, 차단 해제
- **서버 관리**: 공지사항, 저장, 종료

### 👥 사용자 관리
- **역할 기반 접근 제어** (관리자/게스트)
- **세션 기반 인증**
- **비밀번호 해싱** (bcrypt)

## 기술 스택

### 백엔드
- **Flask** (Python 3.x)
- **Flask-SocketIO** (웹소켓 실시간 통신)
- **Waitress** (프로덕션 WSGI 서버, CPU 기반 동적 스레드)
- **SQLite** (데이터베이스)
- **psutil** (프로세스 모니터링, 배치 처리 최적화)
- **bcrypt** (비밀번호 해싱)
- **requests** (HTTP 클라이언트)
- **커스텀 예외 시스템** (11개 예외 클래스)
- **표준 로깅** (파일 로테이션 지원)

### 프론트엔드
- **React** (UI 프레임워크)
- **Vite** (빌드 도구)
- **Axios** (HTTP 클라이언트)
- **Recharts** (차트 라이브러리)
- **Lucide React** (아이콘)
- **TailwindCSS** (스타일링)

### 인프라
- **Windows** (운영 환경)
- **환경 변수** (.env 파일)

## 설치 및 실행

### 1. 의존성 설치

**백엔드:**
```bash
pip install -r requirements.txt
```

**프론트엔드:**
```bash
cd frontend
npm install
cd ..
```

### 2. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 수정하세요:

```bash
copy .env.example .env
```

주요 설정:

**실행 모드:**
- `PRODUCTION`: 프로덕션 모드 여부 (True/False)
  - `False`: 개발 모드 (백엔드 + 프론트엔드 별도 실행)
  - `True`: 프로덕션 모드 (단일 서버로 통합 실행)

**백엔드 (Flask):**
- `FLASK_HOST`: Flask 서버 호스트 (기본: 0.0.0.0)
- `FLASK_PORT`: Flask 서버 포트 (기본: 8080)
- `FLASK_DEBUG`: 디버그 모드 (개발: True, 운영: False)
- `SECRET_KEY`: 세션 암호화 키 (운영 환경에서는 반드시 변경!)

**프론트엔드 (Vite - 개발 모드에서만 사용):**
- `VITE_PORT`: Vite 개발 서버 포트 (기본: 5173)
- 백엔드 URL은 `FLASK_PORT`를 자동으로 사용합니다

### 3. 실행 방법

#### 🔧 개발 모드 (권장 - 개발 시)

**백엔드만 실행 (권장)**
```bash
dev.bat
```

**백엔드 + 프론트엔드 통합 실행**
```bash
dev.bat full
```

**수동 실행**
```bash
# 백엔드 (터미널 1)
cd backend
python -u app.py

# 프론트엔드 (터미널 2)
cd frontend
npm run dev
```

**접속:**
- 프론트엔드: `http://localhost:5173`
- 백엔드 API: `http://localhost:8080`

**특징:**
- ✅ 핫 리로드 (코드 수정 시 자동 새로고침)
- ✅ 빠른 개발 속도
- ✅ 디버깅 용이

---

#### 🚀 프로덕션 모드 (권장 - 배포 시)

**빌드 + 배포 (권장)**
```bash
prod.bat
```

**빌드만**
```bash
prod.bat build
```

**실행만**
```bash
prod.bat run
```

**접속:**
- 통합 서버: `http://localhost:8080`

**특징:**
- ✅ 단일 서버로 실행 (간편한 배포)
- ✅ 최적화된 빌드 (빠른 로딩)
- ✅ Waitress WSGI 서버 사용 (프로덕션 환경 최적화)
- ✅ 멀티스레드 지원 (동시 요청 처리)
- ✅ 자동 .env 파일 관리 (PRODUCTION=True 설정 및 복원)

**주의:**
- `run-production.bat` 실행 시 `.env` 파일의 `PRODUCTION` 값이 자동으로 `True`로 변경됩니다
- 서버 종료 시 자동으로 원래 값으로 복원됩니다
- 수동으로 `.env` 파일을 수정할 필요가 없습니다

### 5. 기본 계정

- **관리자**: `admin` / `admin`
- **게스트**: `guest` / `guest`

⚠️ **보안 주의**: 실서비스 배포 전 반드시 비밀번호를 변경하세요!

## 프로젝트 구조

```
monitoring/
├── backend/                     # Flask 백엔드
│   ├── app.py                  # Flask 애플리케이션 진입점
│   ├── config.py               # 설정 및 경로 관리
│   ├── requirements.txt        # Python 의존성
│   │
│   ├── routes/                 # 웹 페이지 라우트
│   │   └── web.py             # 로그인, 대시보드 등
│   │
│   ├── api/                    # REST API 엔드포인트
│   │   ├── programs.py        # 프로그램 관리 API
│   │   ├── metrics.py         # 리소스 메트릭 API
│   │   └── plugins.py         # 플러그인 관리 API
│   │
│   ├── utils/                  # 유틸리티 함수
│   │   ├── database.py        # SQLite 데이터베이스
│   │   ├── process_manager.py # 프로세스 관리
│   │   ├── process_monitor.py # 프로세스 모니터링
│   │   ├── auth.py            # 인증 및 비밀번호 해싱
│   │   ├── webhook.py         # 웹훅 알림
│   │   └── logger.py          # 로깅
│   │
│   ├── plugins/                # 플러그인 시스템
│   │   ├── base.py            # 플러그인 베이스 클래스
│   │   ├── loader.py          # 플러그인 로더
│   │   └── available/         # 사용 가능한 플러그인
│   │       ├── rcon.py        # RCON Controller
│   │       ├── palworld.py    # Palworld REST API
│   │       └── rest_api.py    # REST API Controller
│   │
│   ├── data/                   # 데이터 저장소 (자동 생성)
│   │   └── monitoring.db      # SQLite 데이터베이스
│   │
│   └── static/                 # 정적 파일
│       └── dist/              # 프론트엔드 빌드 결과
│
├── frontend/                    # React 프론트엔드
│   ├── package.json            # Node.js 의존성
│   ├── vite.config.js          # Vite 설정
│   ├── tailwind.config.js      # TailwindCSS 설정
│   │
│   ├── src/
│   │   ├── main.jsx           # React 진입점
│   │   ├── App.jsx            # 라우팅 설정
│   │   │
│   │   ├── pages/             # 페이지 컴포넌트
│   │   │   ├── LoginPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   └── ProgramDetail.jsx  # 프로그램 상세 페이지
│   │   │
│   │   ├── components/        # 재사용 컴포넌트
│   │   │   ├── ProgramCard.jsx
│   │   │   ├── ResourceChart.jsx
│   │   │   ├── PluginTab.jsx      # 플러그인 탭
│   │   │   └── EditProgramModal.jsx
│   │   │
│   │   └── lib/               # 유틸리티
│   │       └── api.js         # API 클라이언트
│   │
│   └── public/                 # 공개 자산
│
├── .env                        # 환경 변수 (gitignore)
├── .env.example                # 환경 변수 템플릿
├── start.bat                   # Windows 시작 스크립트
├── start.sh                    # Linux/Mac 시작 스크립트
└── README.md                   # 프로젝트 문서
```

## 아키텍처

### 시스템 구성도

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 (브라우저)                      │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────────┐
│              React Frontend (Vite)                       │
│  - 대시보드, 프로그램 관리, 플러그인 UI                   │
│  - 실시간 상태 업데이트 (5초 간격)                       │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Flask Backend (Python)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  API Layer                                       │   │
│  │  - /api/programs  (프로그램 관리)                │   │
│  │  - /api/metrics   (리소스 메트릭)                │   │
│  │  - /api/plugins   (플러그인 관리)                │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Business Logic                                  │   │
│  │  - Process Manager  (프로세스 제어)              │   │
│  │  - Process Monitor  (상태 모니터링)              │   │
│  │  - Plugin Loader    (플러그인 동적 로딩)         │   │
│  │  - Webhook Manager  (알림 전송)                  │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Data Layer                                      │   │
│  │  - SQLite Database                               │   │
│  │    • users (사용자)                              │   │
│  │    • programs (프로그램)                         │   │
│  │    • resource_usage (리소스 사용량)              │   │
│  │    • plugin_configs (플러그인 설정)              │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ psutil
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Windows OS (프로세스)                       │
│  - 관리 대상 프로그램들                                  │
│  - 자식 프로세스 추적 및 제어                            │
└─────────────────────────────────────────────────────────┘
```

### 플러그인 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                  Plugin System                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  PluginBase (Abstract Class)                    │   │
│  │  - get_name()                                    │   │
│  │  - get_description()                             │   │
│  │  - get_config_schema()                           │   │
│  │  - get_actions()                                 │   │
│  │  - execute_action()                              │   │
│  │  - validate_config()                             │   │
│  │  - on_program_start/stop/crash()                 │   │
│  └─────────────────────────────────────────────────┘   │
│                        ▲                                 │
│                        │ 상속                            │
│           ┌────────────┴────────────┬──────────────┐   │
│           │                         │              │   │
│  ┌────────┴────────┐   ┌───────────┴──────┐  ┌───┴────────────┐
│  │  RCON Plugin    │   │ Palworld Plugin  │  │ REST API Plugin│
│  │  - 게임 서버     │   │ - Palworld 전용  │  │ - HTTP 요청    │
│  │  - 명령어 실행   │   │ - REST API 제어  │  │ - 웹훅 전송    │
│  └─────────────────┘   └──────────────────┘  └────────────────┘
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  PluginLoader                                    │   │
│  │  - 플러그인 자동 발견                             │   │
│  │  - 동적 로딩/언로딩                               │   │
│  │  - 생명주기 관리                                  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 데이터베이스 스키마

### users (사용자)
- `id`: INTEGER PRIMARY KEY
- `username`: TEXT UNIQUE
- `password_hash`: TEXT
- `role`: TEXT (admin/guest)

### programs (프로그램)
- `id`: INTEGER PRIMARY KEY
- `name`: TEXT
- `path`: TEXT
- `args`: TEXT
- `pid`: INTEGER
- `webhook_urls`: TEXT

### resource_usage (리소스 사용량)
- `id`: INTEGER PRIMARY KEY
- `program_id`: INTEGER
- `timestamp`: TEXT
- `cpu_percent`: REAL
- `memory_mb`: REAL

### plugin_configs (플러그인 설정)
- `id`: INTEGER PRIMARY KEY
- `program_id`: INTEGER
- `plugin_id`: TEXT
- `config`: TEXT (JSON)
- `enabled`: INTEGER (0/1)

## API 엔드포인트

### 프로그램 관리
- `GET /api/programs` - 프로그램 목록 조회
- `POST /api/programs` - 프로그램 등록
- `PUT /api/programs/<id>` - 프로그램 수정
- `DELETE /api/programs/<id>/delete` - 프로그램 삭제
- `POST /api/programs/<id>/start` - 프로그램 시작
- `POST /api/programs/<id>/stop` - 프로그램 종료
- `POST /api/programs/<id>/restart` - 프로그램 재시작
- `GET /api/programs/status` - 전체 상태 조회

### 리소스 메트릭
- `GET /api/metrics/<id>?hours=24` - 리소스 사용 히스토리

### 플러그인
- `GET /api/plugins/available` - 사용 가능한 플러그인 목록
- `GET /api/plugins/program/<id>` - 프로그램별 플러그인 설정
- `POST /api/plugins/config` - 플러그인 설정 생성
- `PUT /api/plugins/config/<id>` - 플러그인 설정 수정
- `DELETE /api/plugins/config/<id>` - 플러그인 설정 삭제
- `POST /api/plugins/config/<id>/execute` - 플러그인 액션 실행

## 보안

- ✅ **비밀번호 해싱**: bcrypt 사용
- ✅ **세션 기반 인증**: Flask session
- ✅ **역할 기반 접근 제어**: admin/guest
- ✅ **환경 변수 분리**: .env 파일
- ⚠️ **HTTPS**: 운영 환경에서 적용 필요
- ⚠️ **CSRF 보호**: 추가 구현 필요

## 개발 문서

### API 통신 규칙
프론트엔드-백엔드 통신 시 반드시 준수해야 할 규칙과 컨벤션입니다.

📖 **[API 통신 규칙 및 컨벤션](doc/api-conventions.md)**

**주요 내용:**
- API 응답 구조 (목록은 항상 `{key: [...]}` 형태)
- HTTP 상태 코드 사용법
- 에러 처리 가이드
- 네이밍 컨벤션
- 일반적인 실수 및 해결 방법

**새로운 API 추가 시 필수 확인:**
- [ ] API 응답 구조가 규칙을 따르는가?
- [ ] 에러 처리가 되어 있는가?
- [ ] README의 "API 엔드포인트" 섹션에 추가했는가?
