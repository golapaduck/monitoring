# 아키텍처 분석 및 개선 제안

> **모니터링 시스템 스택, 아키텍처, 데이터 처리 로직 상세 분석**

---

## 📊 현재 스택 분석

### 기술 스택

```
Frontend:
- React 18 (UI 프레임워크)
- Vite (번들러, 개발 서버)
- Socket.IO (실시간 통신)
- TailwindCSS (스타일링)

Backend:
- Flask 3.0 (웹 프레임워크)
- SQLite (데이터베이스)
- Waitress (WSGI 서버)
- psutil (시스템 모니터링)
- bcrypt (비밀번호 해싱)

Infrastructure:
- Windows PC (단일 서버)
- Python 3.x
- npm (패키지 관리)
```

### 평가

```
✅ 강점
- 가벼운 스택 (Windows PC 최적화)
- 실시간 통신 (WebSocket)
- 캐싱 전략 (메모리 기반)
- 데이터베이스 연결 풀 (동시성 개선)
- 배치 처리 (성능 최적화)

⚠️ 약점
- SQLite 동시성 제한
- 메모리 기반 캐싱 (서버 재시작 시 손실)
- 대용량 데이터 처리 미흡
- 로그 집계 부재
```

---

## 🏗️ 아키텍처 분석

### 1. 데이터 흐름

```
클라이언트 (React)
    ↓
REST API / WebSocket
    ↓
Flask 백엔드
    ├─ 캐시 확인 (메모리)
    ├─ DB 쿼리 (SQLite)
    ├─ 비즈니스 로직
    └─ 응답 생성
    ↓
데이터베이스 (SQLite)
    ├─ 프로그램 정보
    ├─ 이벤트 로그
    ├─ 리소스 사용량
    └─ 플러그인 설정
```

### 2. 계층 구조

```
Presentation Layer (프론트엔드)
    ↓
API Layer (Flask Blueprint)
    ├─ /api/programs (프로그램 관리)
    ├─ /api/status (상태 조회)
    ├─ /api/metrics (메트릭)
    ├─ /api/plugins (플러그인)
    └─ /api/system (시스템 정보)
    ↓
Business Logic Layer
    ├─ 프로세스 관리
    ├─ 플러그인 실행
    ├─ 웹훅 알림
    └─ 캐싱 전략
    ↓
Data Access Layer
    ├─ 데이터베이스 연결 풀
    ├─ 쿼리 최적화
    └─ 인덱싱
    ↓
Database Layer (SQLite)
```

### 3. 캐싱 전략

```
현재 캐싱:
- 프로그램 목록: 10초 TTL
- 프로그램 상세: 30초 TTL
- 프로그램 상태: 2초 TTL
- 메트릭: 5분 TTL

문제점:
- 메모리 기반 (서버 재시작 시 손실)
- 캐시 무효화 수동 처리
- 분산 환경 미지원
```

### 4. 데이터베이스 설계

```
테이블 구조:
- users: 사용자 정보
- programs: 프로그램 정보
- program_events: 이벤트 로그
- resource_usage: 리소스 사용량 기록
- webhook_urls: 웹훅 URL
- webhook_config: 웹훅 설정
- plugin_configs: 플러그인 설정

인덱스:
- programs(name)
- program_events(program_id, timestamp DESC)
- resource_usage(program_id, timestamp DESC)
- webhook_urls(program_id)
- plugin_configs(program_id)
- users(username)

최적화:
✅ 복합 인덱스 (자주 사용되는 쿼리)
✅ 외래키 제약 (데이터 무결성)
✅ 타임스탬프 인덱싱 (시계열 데이터)
```

---

## 📈 데이터 처리 로직 분석

### 1. 프로그램 상태 조회

```python
# 현재 구현 (programs.py)
1. 캐시 확인 (2초 TTL)
2. 모든 프로그램 조회 (DB)
3. 각 프로그램별 상태 확인
   - PID 확인
   - CPU/메모리 조회
   - 가동 시간 계산
4. 캐시 저장
5. JSON 파일 저장 (동기화용)
6. 응답 반환

성능:
- 캐시 히트: ~10ms
- 캐시 미스: ~100-200ms (프로그램 수에 따라)
```

### 2. 메트릭 조회

```python
# 현재 구현 (metrics.py)
1. 캐시 확인 (5분 TTL)
2. DB에서 시계열 데이터 조회
   - 시간 범위 제한 (최대 168시간)
   - 메모리 최적화
3. 스트리밍 내보내기 지원
   - 배치 처리 (1000개 단위)
   - JSONL 형식

문제점:
- 대용량 데이터 조회 시 메모리 부하
- 실시간 메트릭 업데이트 부재
- 집계 함수 미지원 (평균, 최대값 등)
```

### 3. 플러그인 실행

```python
# 현재 구현 (plugins.py)
1. 플러그인 로더 초기화
2. 플러그인 설정 검증
3. 플러그인 인스턴스 생성
4. 액션 실행
5. 결과 반환

문제점:
- 동기 실행만 지원
- 오류 처리 미흡
- 타임아웃 없음
- 재시도 로직 부재
```

### 4. 웹훅 알림

```python
# 현재 구현 (webhook.py)
1. 이벤트 발생
2. 웹훅 URL 조회
3. HTTP POST 요청
4. 응답 처리

문제점:
- 동기 실행 (블로킹)
- 재시도 없음
- 타임아웃 없음
- 실패 로그 부재
```

---

## 🔍 발견된 문제점

### 1. 성능 문제

#### A. N+1 쿼리 문제
```python
# 문제 코드
for program in programs:
    stats = get_process_stats(program["path"], pid=saved_pid)
    # 각 프로그램마다 별도 쿼리 실행

# 개선: 배치 처리
status_list = get_programs_status_batch(programs)
```

#### B. 메모리 누수
```python
# 캐시가 메모리에만 저장됨
# 서버 재시작 시 모든 캐시 손실
# 대용량 메트릭 조회 시 메모리 부하
```

#### C. 동기 블로킹
```python
# 웹훅, 플러그인이 동기 실행
# 느린 외부 API 호출 시 전체 요청 지연
```

### 2. 데이터 일관성 문제

#### A. PID 동기화
```python
# 문제: PID가 변경되었을 때 감지 지연
# 해결: 실시간 모니터링 필요
```

#### B. 캐시 무효화
```python
# 문제: 수동 캐시 무효화
# 해결: 자동 무효화 전략 필요
```

### 3. 확장성 문제

#### A. SQLite 동시성
```python
# SQLite는 동시 쓰기 제한
# 대용량 데이터 처리 시 병목
```

#### B. 메모리 기반 캐싱
```python
# 분산 환경 미지원
# 캐시 공유 불가능
```

### 4. 모니터링 부재

```python
# 문제점:
- 성능 메트릭 없음
- 에러 추적 미흡
- 로그 집계 부재
- 알림 시스템 없음
```

---

## 💡 개선 제안

### 1. 우선순위 높음 (필수)

#### A. 비동기 처리 도입
```python
# 웹훅, 플러그인을 비동기로 실행
# 타임아웃 설정
# 재시도 로직 추가

from celery import Celery
app = Celery('monitoring')

@app.task(bind=True, max_retries=3)
def send_webhook_async(self, url, data):
    try:
        requests.post(url, json=data, timeout=5)
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

#### B. 캐시 개선
```python
# Redis 도입 (또는 파일 기반 캐시)
# 자동 무효화 전략
# 캐시 통계

from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.cached(timeout=10, key_prefix='programs:')
def get_programs():
    return get_all_programs()
```

#### C. 쿼리 최적화
```python
# N+1 문제 해결
# 배치 조회 확대
# 집계 함수 활용

# 개선 전
for program in programs:
    stats = get_stats(program['id'])

# 개선 후
stats_map = get_all_stats_batch(program_ids)
for program in programs:
    stats = stats_map[program['id']]
```

### 2. 우선순위 중간 (권장)

#### A. 로깅 및 모니터링
```python
# 구조화된 로깅
# 성능 메트릭 수집
# 에러 추적

import structlog
logger = structlog.get_logger()

logger.info(
    "program_started",
    program_id=1,
    pid=1234,
    duration_ms=100
)
```

#### B. 데이터베이스 마이그레이션
```python
# PostgreSQL 검토 (필요시)
# 또는 SQLite 최적화 강화
# 읽기 복제본 고려

# SQLite 최적화
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
```

#### C. API 응답 최적화
```python
# 페이지네이션 추가
# 필드 선택 지원
# 응답 압축

@app.route('/api/programs')
def get_programs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    fields = request.args.get('fields', 'id,name,status').split(',')
    
    # 페이지네이션 + 필드 선택
```

### 3. 우선순위 낮음 (선택)

#### A. 분석 대시보드
```python
# 성능 분석
# 리소스 사용량 추이
# 오류율 모니터링
```

#### B. 자동 스케일링
```python
# 부하에 따른 리소스 조정
# 자동 재시작
```

---

## 📋 개선 로드맵

### Phase 1 (1-2주)
```
✅ 비동기 처리 도입
✅ 캐시 개선 (Redis 또는 파일)
✅ 쿼리 최적화
```

### Phase 2 (2-3주)
```
✅ 로깅 및 모니터링
✅ 데이터베이스 최적화
✅ API 응답 최적화
```

### Phase 3 (3-4주)
```
✅ 분석 대시보드
✅ 자동 스케일링
✅ 성능 튜닝
```

---

## 🎯 권장 즉시 조치

### 1. 웹훅 비동기화 (1시간)
```python
# 현재: 동기 실행 (블로킹)
# 개선: 백그라운드 작업으로 변경
```

### 2. 캐시 TTL 조정 (30분)
```python
# 프로그램 목록: 10초 → 30초
# 메트릭: 5분 → 10분
# 상태: 2초 → 5초
```

### 3. 데이터베이스 최적화 (1시간)
```python
# PRAGMA 설정 추가
# 인덱스 분석
# 쿼리 실행 계획 검토
```

---

## 결론

```
현재 상태:
✅ 기본 기능 완성
✅ Windows PC 최적화
✅ 실시간 통신 구현

개선 필요:
⚠️ 성능 최적화
⚠️ 확장성 개선
⚠️ 모니터링 강화

권장 조치:
1. 비동기 처리 도입
2. 캐시 전략 개선
3. 쿼리 최적화
4. 로깅 강화
```

---

**작성일:** 2025-11-22  
**분석 범위:** 스택, 아키텍처, 데이터 처리 로직  
**상태:** 완료
