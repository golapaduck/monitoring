# Development Progress Log

## 기록 템플릿
- **프로젝트명(Project Name)**: monitoring
- **날짜(Date)**:
- **목표(Objective)**:
- **진행 사항(Progress)**:
- **이슈 & 결정사항(Issues & Decisions)**:
- **다음 할 일(Next Actions)**:

---

## 2025-11-20
- **목표**: Windows에서 운영되는 전용 서버 관제를 위한 시스템 아키텍처 초안 수립 및 문서 구조 마련
- **진행 사항**:
  1. `doc/` 폴더 및 `development-progress.md` 생성
  2. 관제 시스템 전반 요구사항 정리 (상태 수집, 제어, 알림, 대시보드)
  3. 계층형 아키텍처 초안 정의
  4. **프로토타입 스택 확정**: 백엔드는 Flask, 프런트는 HTML/CSS/JS + Bootstrap, 데이터 저장은 JSON 파일
  5. **운영 전략 초안**: Windows 작업 스케줄러로 24시간 구동 및 자동 재시작
- **이슈 & 결정사항**:
  - PowerShell 기반 Windows Service 에이전트 + Flask 백엔드 조합으로 단순화
  - Redis/Timescale DB 대신 JSON 파일 기반 경량 DB를 1차 적용 (후속 확장 대비 구조화 필요)
  - Windows 작업 스케줄러로 백엔드/에이전트 자동 재실행 플로우 구성
  - **역할 정책**: 관리자 계정은 응용 프로그램 등록/종료/실행, 게스트는 상태 조회 및 재부팅만 허용
- **다음 할 일**:
  1. Flask API 명세(로그인, 상태 조회, 제어 명령) 및 JSON 스키마 정의
  2. Windows 작업 스케줄러용 실행 스크립트/설정 매뉴얼 작성
  3. 역할별 UI 흐름(관리자/게스트) 와이어프레임 초안
  4. JSON 기반 데이터 무결성/백업 전략 수립

---

## 2025-11-20 (오후) - 프로토타입 초기 구현
- **목표**: Flask 기반 웹 애플리케이션 뼈대 구축 및 기본 기능 구현
- **진행 사항**:
  1. ✅ Flask 앱 진입점(`app.py`) 작성 완료
     - JSON 기반 데이터 저장소 헬퍼 함수 구현
     - 로그인/로그아웃/대시보드 라우트 구현
     - API 엔드포인트 기본 구조 작성 (`/api/status`, `/api/programs`)
  2. ✅ 로그인 페이지(`templates/login.html`) 작성
     - Bootstrap 5 기반 반응형 디자인
     - 그라데이션 배경 및 카드 레이아웃
  3. ✅ 대시보드 페이지(`templates/dashboard.html`) 작성
     - 관리자/게스트 역할별 UI 분기
     - 프로그램 목록 표시 및 추가 모달
     - 실시간 상태 업데이트 스크립트 (30초 주기)
  4. ✅ 프로젝트 문서화
     - `README.md`: 설치/실행 가이드, 프로젝트 구조 설명
     - `requirements.txt`: Flask 의존성 정의
     - `.gitignore`: Python/Flask 표준 무시 파일 설정
  5. ✅ 기본 데이터 초기화 로직
     - `data/users.json`: admin/guest 기본 계정 자동 생성
     - `data/programs.json`: 빈 프로그램 목록 초기화
     - `data/status.json`: 상태 데이터 구조 준비
- **이슈 & 결정사항**:
  - 비밀번호는 현재 평문 저장 (프로토타입 단계, 추후 bcrypt 등으로 해싱 필요)
  - SECRET_KEY는 하드코딩 상태 (실서비스 시 환경변수로 분리 필요)
  - 프로그램 실행/종료 제어 로직은 다음 단계에서 PowerShell 연동으로 구현 예정
- **다음 할 일**:
  1. PowerShell 에이전트 스크립트 작성 (프로세스 상태 수집)
  2. Flask에서 PowerShell 명령 실행 기능 구현 (subprocess 활용)
  3. Windows 작업 스케줄러 설정 가이드 문서 작성
  4. 프로그램 상태 실시간 업데이트 로직 완성

---

## 2025-11-20 (저녁) - 핵심 기능 구현 완료
- **목표**: 프로그램 제어 기능 구현 및 24시간 운영 준비
- **진행 사항**:
  1. ✅ 환경변수 분리 (`.env` 파일)
     - `FLASK_HOST`, `FLASK_PORT`, `FLASK_DEBUG`, `SECRET_KEY` 환경변수로 관리
     - `.env.example` 템플릿 파일 생성
     - `python-dotenv` 패키지 추가
  2. ✅ 프로그램 제어 기능 구현
     - `psutil` 라이브러리로 프로세스 상태 확인
     - `subprocess` + PowerShell로 프로그램 실행/종료
     - 재시작 기능 (종료 → 1초 대기 → 실행)
  3. ✅ API 엔드포인트 추가
     - `POST /api/programs/<id>/start`: 프로그램 실행 (관리자만)
     - `POST /api/programs/<id>/stop`: 프로그램 종료 (관리자만)
     - `POST /api/programs/<id>/restart`: 프로그램 재시작 (게스트 가능)
     - `DELETE /api/programs/<id>/delete`: 프로그램 삭제 (관리자만)
     - `GET /api/programs/status`: 실시간 상태 조회 (모든 사용자)
  4. ✅ 대시보드 UI 업데이트
     - 프로그램별 실행/종료/재시작/삭제 버튼 추가
     - 5초마다 자동 상태 업데이트
     - 실행 중/중지됨 상태 배지 색상 표시 (초록/빨강)
     - 요약 카운트 (등록된 프로그램, 실행 중, 중지됨)
  5. ✅ Windows 작업 스케줄러 준비
     - `scripts/start_monitoring.ps1`: 자동 시작 스크립트 작성
     - 로그 디렉토리 자동 생성 및 일별 로그 파일
     - 중복 실행 방지 로직
     - `doc/windows-task-scheduler-guide.md`: 상세 설정 가이드 작성
  6. ✅ 문서 업데이트
     - `README.md`: 환경변수 설정 및 작업 스케줄러 가이드 추가
     - `.gitignore`: `.env` 파일 제외 설정
- **이슈 & 결정사항**:
  - PowerShell 실행 정책 문제 대비 `-ExecutionPolicy Bypass` 옵션 사용
  - 프로세스 감지는 실행 파일명 기준 (경로 전체 비교는 권한 문제로 제한적)
  - 상태 업데이트 주기를 30초 → 5초로 단축 (더 빠른 피드백)
  - 게스트 계정도 재시작 기능 사용 가능하도록 권한 부여
- **다음 할 일**:
  1. 실제 테스트 (메모장 등 간단한 프로그램으로 동작 확인)
  2. 비밀번호 해싱 기능 추가 (bcrypt)
  3. 프로그램 실행 로그 기록 (누가, 언제, 무엇을)
  4. 알림 기능 추가 (프로그램 비정상 종료 시 이메일/메신저)
  5. 시스템 리소스 모니터링 (CPU, 메모리, 디스크)

---

## 2025-11-20 (밤) - 코드 리팩토링 (Blueprint 기반 모듈화)
- **목표**: 확장성을 고려한 코드 구조 개선
- **진행 사항**:
  1. ✅ Blueprint 기반 모듈 분리
     - `routes/web.py`: 웹 페이지 라우트 (로그인, 대시보드)
     - `api/programs.py`: 프로그램 제어 API
     - `api/status.py`: 상태 조회 API (향후 시스템 리소스 확장 대비)
  2. ✅ 유틸리티 함수 분리
     - `utils/process_manager.py`: 프로세스 관리 함수 모듈화
     - 재사용성 및 테스트 용이성 향상
  3. ✅ app.py 리팩토링
     - 핵심 로직만 유지 (설정, 초기화, Blueprint 등록)
     - 라우트 및 API 로직은 각 모듈로 분산
     - 코드 라인 수 348줄 → 117줄로 감소
  4. ✅ 문서 업데이트
     - README.md: 새로운 프로젝트 구조 반영
     - 모듈별 역할 명시
- **이슈 & 결정사항**:
  - Blueprint URL prefix 설정: `/api/programs`, `/api/status`
  - 순환 참조 방지를 위해 utils 모듈은 app.py에 의존하지 않도록 설계
  - 향후 확장 시 새로운 Blueprint 추가만으로 기능 확장 가능
- **아키텍처 개선 효과**:
  - **모듈화**: 기능별로 파일 분리되어 유지보수 용이
  - **확장성**: 새로운 API나 라우트 추가 시 기존 코드 수정 최소화
  - **테스트 용이성**: 각 모듈을 독립적으로 테스트 가능
  - **가독성**: 파일당 코드 라인 수 감소로 이해하기 쉬움
- **다음 할 일**:
  1. 실제 테스트 및 동작 확인
  2. 각 모듈별 단위 테스트 작성
  3. 에러 핸들링 개선 (커스텀 에러 페이지)
  4. 로깅 시스템 통합 (Python logging 모듈)

---

## 2025-11-22 (새벽) - Phase 1 핵심 기능 강화
- **목표**: 보안, 안정성, 사용성 개선을 위한 6가지 핵심 기능 구현
- **진행 사항**:
  1. ✅ **보안 강화** (비밀번호 해싱 + 세션 관리)
     - bcrypt를 사용한 비밀번호 해싱 기능 추가
     - 기존 평문 비밀번호 자동 마이그레이션
     - 세션 타임아웃 설정 (기본 1시간)
     - 세션 쿠키 보안 설정 (HttpOnly, SameSite)
     - `utils/auth.py` 신규 생성
  
  2. ✅ **모니터링 로직 개선** (PID 우선 확인)
     - PID 기반 프로세스 추적으로 정확도 향상
     - PID가 있으면 먼저 확인하고, 없으면 프로그램 이름으로 검색
     - 프로그램 시작/재시작 시 PID 자동 저장
     - 프로그램 종료 시 PID 자동 제거
     - 상태 조회 시 PID 자동 업데이트 및 동기화
  
  3. ✅ **경로 유효성 체크**
     - 프로그램 등록/수정 시 경로 유효성 자동 검증
     - 파일 존재 여부, 실행 가능 여부, 권한 확인
     - 경로 자동 정규화 (절대 경로로 변환)
     - 프런트엔드용 경로 검증 API 엔드포인트 추가
     - `utils/path_validator.py` 신규 생성
     - 지원 파일 형식: .exe, .bat, .cmd, .ps1, .jar, .py
  
  4. ✅ **강력한 프로세스 제어** (Taskkill /T)
     - 자식 프로세스까지 완전히 종료하는 강제 종료 기능
     - Windows taskkill 명령어 사용 (/F /T 옵션)
     - taskkill 실패 시 psutil로 자동 폴백
     - API에서 force 파라미터로 강제 종료 선택 가능
  
  5. ✅ **다중 웹훅 시스템** (프로그램당 여러 웹훅)
     - 하나의 프로그램에 여러 개의 웹훅 URL 연결 가능
     - 단일 URL과 다중 URL 모두 지원 (하위 호환성 유지)
     - 모든 웹훅 URL에 비동기로 알림 전송
     - 프로그램 등록/수정 시 webhook_urls 리스트로 저장
  
  6. ✅ **파일 탐색기 연동** (API)
     - 프런트엔드에서 파일 시스템 탐색 가능
     - 디렉토리 목록 조회, 파일 검색, 자주 사용하는 경로 제공
     - 실행 가능한 파일 자동 감지
     - 관리자 전용 API (보안)
     - `api/file_explorer.py` 신규 생성

- **이슈 & 결정사항**:
  - bcrypt 라이브러리 추가 (requirements.txt)
  - 세션 타임아웃은 환경변수로 설정 가능 (SESSION_LIFETIME)
  - PID 추적으로 동일 이름 프로세스 구분 가능
  - 경로 검증으로 잘못된 파일 등록 방지
  - 강제 종료는 선택적 기능 (기본은 일반 종료)
  - 웹훅 URL은 리스트 형태로 저장 (하위 호환성 유지)
  - 파일 탐색기는 관리자만 접근 가능

- **커밋 내역**:
  1. `d6564e3` - Feat: 보안 강화 (비밀번호 해싱 및 세션 관리)
  2. `43bb5d5` - Feat: 모니터링 로직 개선 (PID 우선 확인)
  3. `0bf414c` - Feat: 경로 유효성 체크
  4. `af983b8` - Feat: 강력한 프로세스 제어 (Taskkill /T)
  5. `7d2eb7e` - Feat: 다중 웹훅 시스템 (프로그램당 여러 웹훅)
  6. `a62d06e` - Feat: 파일 탐색기 연동 (API)

- **다음 할 일**:
  1. 프런트엔드 UI 개선 (파일 탐색기 모달 구현)
  2. 다중 웹훅 설정 UI 추가
  3. 강제 종료 버튼 추가
  4. 실제 서버 환경에서 테스트
  5. 문서 업데이트 (API 명세서)

---

## 시스템 아키텍처 초안

### 1. 전체 구조 개요 (경량 프로토타입)
```
[Windows Agent Service] <--> [Flask API & Controller] <--> [JSON Data Store]
                                              |
                                              v
                                   [Bootstrap Web Dashboard]
                                              |
                                              v
                              [Control Actions & Windows Scheduler]
```

### 2. 계층별 책임
1. **Agent Layer (Windows Service/Powershell)**
   - 서버별 필수 프로세스/서비스 상태, CPU·메모리 간단 지표 수집
   - Flask API와 로컬 HTTP/Named Pipe로 통신, 실패 시 백오프 재시도
   - Windows 작업 스케줄러에 의해 재기동 스크립트 등록

2. **Flask API & Controller**
   - 인증/인가: 관리자·게스트 역할을 JWT 또는 세션으로 구분
   - 상태 조회, 재부팅 명령, 프로그램 등록/실행/종료 REST Endpoint 제공
   - JSON 파일 읽기/쓰기 래퍼를 통해 데이터 영속화 수행

3. **JSON Data Store**
   - 사용자, 프로그램 목록, 상태 로그를 구조화된 JSON으로 관리
   - 주기적 백업 및 파일 잠금 전략 필요 (threading.Lock 활용)

4. **Bootstrap Web Dashboard (HTML/CSS/JS)**
   - 게스트: 프로그램 상태 조회 + 재부팅 버튼만 노출
   - 관리자: 프로그램 등록/삭제, 실행/종료 제어 UI 추가
   - Fetch API로 Flask Endpoint 호출, Bootstrap 컴포넌트로 반응형 구성

5. **Control Actions & Windows Scheduler**
   - Flask에서 PowerShell 스크립트 실행, 지정된 응용 프로그램 프로세스 제어
   - 작업 스케줄러가 Flask/Agent 프로세스를 24시간 모니터링 후 중단 시 재시작

6. **Notification/Logging (향후)**
   - 초기에는 로컬 로그 파일, 추후 이메일/메신저 연동 검토
   - 비정상 종료 시 작업 스케줄러 + 로그를 통해 추적

### 3. 데이터 흐름 요약
1. Agent가 30초 주기로 상태 수집 → Flask API에 HTTP POST
2. Flask가 JSON 파일에 상태 기록 및 캐시 업데이트
3. 게스트/관리자 UI가 주기적으로 Fetch로 상태 조회
4. 게스트는 재부팅 요청만 수행, Flask가 PowerShell 스크립트 호출
5. 관리자는 등록된 앱을 JSON에 추가·수정하고 실행/종료 명령을 발행
6. Windows 작업 스케줄러가 Flask/Agent 프로세스를 감시하고 중단 시 재실행

### 4. 보안 및 성능 고려사항
- 에이전트 인증: 최소한의 API Key + 서명된 토큰으로 경량 인증 (추후 강화 대비)
- 데이터 암호화: 로컬 환경이나 VPN 내 사용을 가정하되, HTTPS(자체 서명 인증서) 적용
- 성능: 단일 서버 기준 Flask 멀티스레드 + 파일 I/O 잠금으로 동시성 관리
- 장애 대응: Windows 작업 스케줄러 기반 자동 재시작 + JSON 파일 주기적 백업
- 확장성: 차후 필요 시 PostgreSQL/Redis로 마이그레이션 가능한 데이터 추상화 계층 유지

### 5. 향후 문서화 체크리스트
- 통신 프로토콜 명세(API 스키마)
- JSON 스키마 정의(사용자/프로그램/상태 로그)
- 역할별 UI 플로우 차트
- Windows 작업 스케줄러 구성 가이드
- 운영 절차(배포, 롤백, DR)
