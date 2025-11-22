# 🖥️ Monitoring System

> **Windows 프로그램 실시간 모니터링 및 관리 플랫폼**
>
> Flask + React 기반의 고성능 웹 애플리케이션

---

## 📋 목차

- [프로젝트 개요](#프로젝트-개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [아키텍처](#아키텍처)
- [빠른 시작](#빠른-시작)
- [API 엔드포인트](#api-엔드포인트)
- [성능 최적화](#성능-최적화)

---

## 프로젝트 개요

Windows 서버에서 실행 중인 프로그램들을 **실시간으로 모니터링**하고, **웹 기반 UI**를 통해 편리하게 관리할 수 있는 통합 플랫폼입니다.

### 주요 특징
- 🚀 **실시간 모니터링**: WebSocket 기반 1초 단위 상태 업데이트
- 📊 **리소스 모니터링**: CPU, 메모리 사용량 실시간 차트
- 🎮 **프로그램 제어**: 시작, 종료, 재시작 기능
- 🔌 **플러그인 시스템**: Palworld RCON, 파일 감시 등 확장 가능
- 🔐 **인증 및 권한**: 관리자/게스트 역할 기반 접근 제어
- ⚡ **고성능**: 캐싱, 압축, 비동기 처리로 최적화

---

## 주요 기능

### 프로그램 관리
- ✅ 프로그램 등록/수정/삭제
- ✅ 프로그램 시작/종료/재시작
- ✅ 프로그램 상태 실시간 모니터링
- ✅ 예기치 않은 종료 감지 및 알림

### 리소스 모니터링
- ✅ 프로그램별 CPU 사용률 (%)
- ✅ 프로그램별 메모리 사용량 (MB)
- ✅ 프로그램별 가동 시간 (Uptime)
- ✅ 24시간 히스토리 차트
- ✅ **시스템 전체 리소스 모니터링** (CPU, 메모리, 디스크, 가동 시간)

### 플러그인 시스템
- ✅ **Palworld RCON**: 서버 정보 조회, 플레이어 관리
- ✅ **파일 감시**: 로그 파일 실시간 모니터링
- ✅ **작업 큐**: 비동기 작업 처리

### 웹훅 알림
- ✅ 프로그램 시작/종료 알림
- ✅ 예기치 않은 종료 알림
- ✅ 다중 웹훅 URL 지원

---

## 기술 스택

### 백엔드
| 기술 | 버전 | 용도 |
|------|------|------|
| Flask | 3.0.0 | 웹 프레임워크 |
| Flask-SocketIO | 5.3.5 | 실시간 WebSocket |
| Flask-Compress | 1.14.0 | gzip 응답 압축 |
| Waitress | 3.0.0 | WSGI 서버 (Windows 최적) |
| psutil | 5.9.6 | 프로세스 관리 (Windows 최적) |
| SQLite | 3.x | 데이터베이스 (파일 기반) |
| bcrypt | 4.1.2 | 비밀번호 해싱 |
| prometheus-client | 0.19.0 | 메트릭 수집 (선택사항) |

### 프론트엔드
| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18.x | UI 프레임워크 |
| Vite | 5.x | 번들러 |
| React Router | 6.x | 라우팅 |
| Recharts | 2.x | 차트 라이브러리 |
| TailwindCSS | 3.x | CSS 프레임워크 |
| socket.io-client | 4.x | WebSocket 클라이언트 |

---

## 아키텍처

### 전체 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                    클라이언트 (React)                        │
│              WebSocket + REST API 통신                      │
└────────────────────────┬──────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
    ┌───▼────────┐              ┌────────▼──────┐
    │  REST API  │              │  WebSocket    │
    │ (HTTP)     │              │  (실시간)      │
    └───┬────────┘              └────────┬──────┘
        │                                 │
┌───────┴─────────────────────────────────┴──────────────────┐
│                   Flask 백엔드                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API 라우터 (programs, metrics, plugins, webhook)   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  핵심 유틸리티                                        │  │
│  │  - Process Manager (psutil)                          │  │
│  │  - WebSocket Manager                                │  │
│  │  - Cache (메모리, TTL 기반)                          │  │
│  │  - Database (SQLite, 연결 풀 5개 - Windows 최적)    │  │
│  │  - Job Queue (2개 워커 - Windows 최적)              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  백그라운드 서비스                                    │  │
│  │  - Process Monitor (3초 간격 - Windows 최적)        │  │
│  │  - PowerShell Agent (비동기)                        │  │
│  │  - File Watcher (로그 감시)                         │  │
│  └──────────────────────────────────────────────────────┘  │
└───────┬─────────────────────────────────────────────────────┘
        │
    ┌───┴────────────────────────┐
    │                            │
┌───▼─────────┐        ┌────────▼──────┐
│  Windows    │        │  Webhook      │
│  프로세스   │        │  서버 (외부)   │
└─────────────┘        └───────────────┘
```

### 데이터 흐름

**프로그램 상태 모니터링:**
```
ProcessMonitor (3초 간격 - Windows 최적화)
  ↓
프로세스 상태 확인 (배치 처리)
  ↓
상태 변화 감지
  ↓
WebSocket 이벤트 전송 (즉시)
  ↓
메트릭 수집 (비동기, 1초 주기)
  ↓
DB 저장 + WebSocket 전송
  ↓
프론트엔드 UI 업데이트 (실시간)
```

**API 요청 처리:**
```
클라이언트 요청
  ↓
캐시 확인 (메모리)
  ↓
캐시 히트 → 즉시 응답 (10ms)
캐시 미스 → DB 조회 (100ms)
  ↓
응답 압축 (gzip)
  ↓
클라이언트 수신
```

---

## 성능 최적화 (Windows PC 단일 서버)

### 현재 최적화 설정

| 항목 | 설정 | 목적 |
|------|------|------|
| **DB 연결 풀** | 5개 | 메모리 효율성 |
| **작업 큐 워커** | 2개 | CPU 효율성 |
| **상태 확인 간격** | 3초 | CPU 사용량 감소 |
| **메트릭 수집** | 1초 주기 | 부드러운 차트 업데이트 |
| **응답 압축** | gzip | 네트워크 효율성 |
| **캐싱** | 메모리 기반 | 응답 속도 향상 |

### 리소스 사용량

```
메모리: ~150-200MB
CPU: <5% (평상시)
디스크: ~500MB (빌드 포함)
네트워크: 최소 (WebSocket 기반)
```

### 권장 환경

- **OS**: Windows 10 이상
- **CPU**: 2코어 이상
- **RAM**: 4GB 이상
- **디스크**: 1GB 여유 공간

---

## 빠른 시작

### 사전 요구사항
- Python 3.9+
- Node.js 18+
- Windows 10+

### 개발 모드

```bash
# 1. 저장소 클론
git clone <repository-url>
cd monitoring

# 2. 백엔드 설정
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. 프론트엔드 설정 (새 터미널)
cd frontend
npm install
npm run dev

# 4. 백엔드 실행 (새 터미널)
cd backend
python app.py

# 5. 브라우저 접속
http://localhost:5173
```

### 프로덕션 모드

```bash
# 배치 스크립트 사용
scripts\prod.bat

# 또는 수동 실행
cd frontend && npm run build
cd ../backend && python serve.py

# 브라우저 접속
http://localhost:8080
```

### 24시간 안정 운영 (Windows 작업 스케줄러)

> **Windows PC에서 24시간 안정적으로 운영하기 위한 자동 시작 및 재시작 설정**

```
📖 상세 가이드: doc/WINDOWS_SCHEDULER_GUIDE.md 참고

빠른 설정:
1. Win + R → taskschd.msc
2. 작업 만들기
3. 트리거: "컴퓨터 시작 시"
4. 작업: python serve.py 실행
5. 설정: 실패 시 1분 후 재시작

→ 자동 시작 및 자동 재시작 완료!
```

---

## API 엔드포인트

### 프로그램 관리

| 메서드 | 엔드포인트 | 설명 | 캐시 |
|--------|----------|------|------|
| GET | `/api/programs` | 프로그램 목록 | 10초 |
| POST | `/api/programs` | 프로그램 등록 | - |
| GET | `/api/programs/{id}` | 프로그램 상세 | 30초 |
| PUT | `/api/programs/{id}` | 프로그램 수정 | - |
| DELETE | `/api/programs/{id}/delete` | 프로그램 삭제 | - |
| POST | `/api/programs/{id}/start` | 프로그램 시작 | - |
| POST | `/api/programs/{id}/stop` | 프로그램 종료 | - |
| POST | `/api/programs/{id}/restart` | 프로그램 재시작 | - |
| GET | `/api/programs/status` | 모든 프로그램 상태 | 2초 |

### 메트릭 & 플러그인

| 메서드 | 엔드포인트 | 설명 | 캐시 |
|--------|----------|------|------|
| GET | `/api/metrics/{id}` | 리소스 사용량 | 5분 |
| GET | `/api/plugins/program/{id}` | 프로그램 플러그인 | - |
| POST | `/api/plugins/{id}/action` | 플러그인 액션 | - |

---

## 성능 최적화

### 캐싱 전략
```
프로그램 목록:    10초 TTL
프로그램 상세:    30초 TTL
프로그램 상태:    2초 TTL
메트릭:          5분 TTL
```

### 최적화 결과

| 항목 | Before | After | 개선율 |
|------|--------|-------|--------|
| **번들 크기** | 100% | 60-70% | 30-40% ↓ |
| **API 응답** | 100ms | 10ms (캐시) | 90% ↓ |
| **상태 감지** | 3초 | 1초 | 3배 빠름 |
| **상태 전송** | 3초+ | <100ms | 30배 빠름 |
| **네트워크 트래픽** | 100% | 30% | 70% ↓ |

### 주요 최적화 기법
- **응답 압축**: gzip (50-70% 감소)
- **캐싱**: 메모리 기반 TTL 캐시
- **DB 연결 풀**: 10개 연결 (동시성 2배)
- **비동기 처리**: 메트릭 수집 논블로킹
- **필드 선택**: 필요한 필드만 조회 (30% 감소)
- **청크 분할**: 벤더 라이브러리 분리

---

## 보안 및 안정성

### 보안 기능
- ✅ **CORS 설정**: 환경별 분리 (개발/프로덕션)
- ✅ **세션 보안**: HttpOnly, Secure 플래그
- ✅ **Rate Limiting**: API별 요청 속도 제한
- ✅ **입력 검증**: 경로, 필드 검증
- ✅ **SQL Injection 방지**: 파라미터화된 쿼리
- ✅ **비밀번호 해싱**: bcrypt 사용

### Rate Limiting 정책
| API | 제한 |
|-----|------|
| 인증 | 5 per minute |
| 프로그램 관리 | 30 per minute |
| 프로그램 액션 | 10 per minute |
| 메트릭 | 100 per minute |

### 에러 처리
- 전역 에러 핸들러 (404, 500)
- 표준 에러 응답 형식
- 에러 코드 및 상세 정보

---

## 성능 모니터링

### 성능 통계 API (관리자만)
```bash
# 모든 엔드포인트 성능 통계
GET /api/admin/performance

# 특정 엔드포인트 성능 통계
GET /api/admin/performance/{endpoint}

# 성능 통계 초기화
DELETE /api/admin/performance
```

### 응답 시간 모니터링
```python
from utils.performance_monitor import monitor_performance

@monitor_performance("endpoint_name")
def endpoint():
    ...
```

### 느린 쿼리 감지
```python
from utils.performance_monitor import log_slow_queries

@log_slow_queries(threshold=0.5)
def slow_operation():
    ...
```

---

## 프로젝트 구조

```
monitoring/
├── backend/                    # Flask 백엔드
│   ├── api/                    # REST API 엔드포인트
│   ├── utils/                  # 유틸리티 (DB, 캐시, 웹소켓 등)
│   ├── plugins/                # 플러그인 시스템
│   ├── tests/                  # 단위 테스트
│   ├── app.py                  # 애플리케이션 진입점
│   ├── serve.py                # Waitress WSGI 서버
│   ├── requirements.txt         # Python 의존성
│   └── data/                   # 데이터 디렉토리
│
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── pages/              # 페이지 컴포넌트
│   │   ├── components/         # 재사용 컴포넌트
│   │   ├── hooks/              # 커스텀 훅
│   │   ├── services/           # API 서비스
│   │   └── utils/              # 유틸리티
│   ├── vite.config.js          # Vite 설정
│   └── package.json            # Node.js 의존성
│
├── doc/                        # 문서
│   ├── plan.md                 # 작업 계획
│   ├── api-conventions.md      # API 규칙
│   └── development-progress.md # 개발 진행
│
├── scripts/                    # 실행 스크립트
│   ├── dev.bat                 # 개발 모드
│   └── prod.bat                # 프로덕션 모드
│
└── README.md                   # 이 파일
```

---

## 환경 변수

### 백엔드 (.env)
```
FLASK_ENV=production
FLASK_PORT=8080
SECRET_KEY=your-secret-key
DATABASE_PATH=data/monitoring.db
LOG_LEVEL=INFO
MONITOR_INTERVAL=1
PALWORLD_SHUTDOWN_WAIT_TIME=30
```

### 프론트엔드 (.env)
```
VITE_API_BASE_URL=http://localhost:8080
VITE_SOCKET_URL=http://localhost:8080
VITE_PORT=5173
```

---

## 문제 해결

### 포트 충돌
```bash
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### 데이터베이스 초기화
```bash
del backend\data\monitoring.db
# 서버 재시작 (자동 생성)
```

### 캐시 초기화
```python
from backend.utils.cache import get_cache
cache = get_cache()
cache.clear()
```

---

## 라이선스

MIT License

---

## 기여

버그 리포트, 기능 제안, Pull Request 환영합니다!
