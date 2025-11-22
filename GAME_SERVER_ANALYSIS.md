# 게임 서버 환경 심층 분석

> **단일 PC에서 게임 서버와 함께 구동되는 모니터링 시스템 분석**

---

## 🎮 환경 분석

### 시스템 구성

```
단일 Windows PC
├─ 게임 서버 (주 목적)
│  ├─ Palworld Server (예시)
│  ├─ Minecraft Server
│  ├─ ARK Server
│  └─ 기타 게임 서버들
│
└─ 모니터링 시스템 (보조)
   ├─ Flask Backend (Python)
   ├─ React Frontend (Node.js)
   ├─ SQLite Database
   └─ Process Monitor
```

### 리소스 경쟁 상황

```
CPU:
- 게임 서버: 70-90% (게임 로직, 물리 연산)
- 모니터링: 5-10% (프로세스 체크, API 처리)
→ 총 사용률: 75-100%

메모리:
- 게임 서버: 4-8GB (플레이어 수에 따라)
- 모니터링: 200-500MB (캐시, 메트릭)
→ 총 사용량: 4.2-8.5GB

디스크:
- 게임 서버: 읽기/쓰기 빈번 (세이브 파일)
- 모니터링: 로그, 메트릭 저장
→ I/O 경쟁 발생 가능

네트워크:
- 게임 서버: 플레이어 연결 (우선순위 높음)
- 모니터링: API 요청, 웹훅
→ 대역폭 경쟁
```

---

## ⚠️ 심각한 문제점

### 1. 리소스 경쟁 (Critical)

#### A. CPU 경쟁
```python
# 현재 문제
프로세스 모니터: 3초마다 체크
- PowerShell 실행 (CPU 사용)
- psutil 조회 (CPU 사용)
- 메트릭 수집 (1초마다)

게임 서버가 CPU를 많이 사용할 때:
→ 모니터링 시스템이 추가 부하 발생
→ 게임 서버 성능 저하
→ 플레이어 경험 악화 (렉, 딜레이)

# 개선 필요
- 모니터링 간격 조정 (동적)
- CPU 사용률 기반 스로틀링
- 우선순위 낮추기
```

#### B. 메모리 경쟁
```python
# 현재 문제
메모리 기반 캐싱:
- 프로그램 목록 캐시
- 메트릭 캐시
- 상태 캐시

게임 서버 메모리 부족 시:
→ 모니터링 시스템 캐시가 메모리 점유
→ 게임 서버 스왑 발생
→ 심각한 성능 저하

# 개선 필요
- 캐시 크기 제한
- 메모리 압박 감지
- 자동 캐시 정리
```

#### C. 디스크 I/O 경쟁
```python
# 현재 문제
SQLite 쓰기:
- 메트릭 저장 (1초마다)
- 이벤트 로그
- 리소스 사용량

게임 서버 세이브 시:
→ 디스크 I/O 경쟁
→ 게임 서버 저장 지연
→ 데이터 손실 위험

# 개선 필요
- 배치 쓰기 (버퍼링)
- 쓰기 간격 조정
- WAL 모드 활성화
```

### 2. 프로세스 간섭 (High)

#### A. 게임 서버 종료 감지
```python
# 현재 문제
게임 서버가 정상 종료 중일 때:
- 모니터링이 "크래시"로 오인
- 자동 재시작 시도
- 게임 서버 종료 방해

# 실제 시나리오
1. 관리자가 게임 서버 종료 시작 (30초 대기)
2. 모니터링이 3초 후 "크래시" 감지
3. 웹훅 알림 발송
4. 자동 재시작 시도 (설정된 경우)
5. 게임 서버 정상 종료 방해

# 개선 필요
- 정상 종료 감지 (Graceful Shutdown)
- 종료 대기 시간 설정
- 플러그인 연동 (API 기반 종료)
```

#### B. 리소스 측정 부정확
```python
# 현재 문제
psutil.cpu_percent(interval=0.1):
- 0.1초 샘플링
- 순간 값만 측정
- 게임 서버 부하 패턴 미반영

게임 서버 특성:
- 틱 기반 동작 (주기적 부하)
- 플레이어 접속 시 스파이크
- 세이브 시 I/O 스파이크

# 개선 필요
- 샘플링 간격 조정
- 평균값 계산
- 피크 값 추적
```

### 3. 동시성 문제 (High)

#### A. SQLite 잠금
```python
# 현재 문제
SQLite는 동시 쓰기 제한:
- 메트릭 저장 (1초마다)
- 이벤트 로그
- 프로그램 상태 업데이트

게임 서버 이벤트 발생 시:
→ 여러 쓰기 작업 동시 발생
→ 데이터베이스 잠금
→ 쓰기 지연 또는 실패

# 개선 필요
- WAL 모드 활성화
- 쓰기 큐 도입
- 배치 처리
```

#### B. 웹훅 블로킹
```python
# 현재 문제
웹훅이 동기 실행:
- HTTP 요청 대기
- 타임아웃 없음
- 재시도 없음

게임 서버 크래시 시:
→ 웹훅 발송 시도
→ 외부 서버 응답 대기
→ 모니터링 시스템 블로킹
→ 다른 게임 서버 모니터링 지연

# 개선 필요
- 비동기 웹훅
- 타임아웃 설정 (5초)
- 백그라운드 작업
```

---

## 🔥 게임 서버 특화 문제

### 1. 게임 서버 특성 미고려

#### A. 틱 기반 동작
```python
# 게임 서버 특성
- 20 TPS (Tick Per Second)
- 매 틱마다 CPU 스파이크
- 플레이어 많을수록 부하 증가

# 현재 모니터링
- 0.1초 샘플링 (부정확)
- 순간 값만 측정
- 평균 부하 미반영

# 개선 필요
- 틱 주기 고려한 샘플링
- 이동 평균 계산
- 부하 패턴 분석
```

#### B. 플레이어 수 미추적
```python
# 현재 문제
게임 서버 부하 원인 파악 불가:
- CPU 높음 → 플레이어 많음? 버그?
- 메모리 높음 → 플레이어 많음? 누수?

# 개선 필요
- 플레이어 수 추적
- 플레이어당 리소스 계산
- 이상 패턴 감지
```

#### C. 세이브 주기 미고려
```python
# 게임 서버 특성
- 5분마다 자동 세이브
- 세이브 시 디스크 I/O 스파이크
- 메모리 사용량 증가

# 현재 모니터링
- 세이브 시점 미인지
- 일시적 스파이크를 "문제"로 오인

# 개선 필요
- 세이브 주기 설정
- 세이브 시 메트릭 필터링
- 정상 패턴 학습
```

### 2. 플러그인 시스템 한계

#### A. 동기 실행
```python
# 현재 문제
플러그인 액션 실행:
- 동기 실행 (블로킹)
- 타임아웃 없음
- 게임 서버 API 호출 대기

예: Palworld 서버 종료
1. 플러그인 호출
2. REST API 요청 (30초 대기)
3. 응답 대기
4. 모니터링 시스템 블로킹

# 개선 필요
- 비동기 플러그인 실행
- 타임아웃 설정
- 백그라운드 작업
```

#### B. 에러 처리 미흡
```python
# 현재 문제
플러그인 실패 시:
- 에러만 로그
- 재시도 없음
- 폴백 없음

게임 서버 API 장애 시:
→ 플러그인 실패
→ 수동 개입 필요

# 개선 필요
- 재시도 로직 (3회)
- 폴백 전략
- 알림 강화
```

---

## 💡 게임 서버 환경 최적화 제안

### 1. 우선순위 최고 (즉시 적용)

#### A. CPU 우선순위 조정
```python
# 모니터링 프로세스 우선순위 낮추기
import psutil
import os

# 현재 프로세스
p = psutil.Process(os.getpid())

# 우선순위 낮추기 (BELOW_NORMAL)
p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

print("✅ 모니터링 프로세스 우선순위 낮춤 (게임 서버 우선)")
```

#### B. 동적 모니터링 간격
```python
# CPU 사용률에 따라 모니터링 간격 조정
def get_adaptive_interval():
    cpu_usage = psutil.cpu_percent(interval=1)
    
    if cpu_usage > 90:
        return 10  # CPU 높음 → 10초 간격
    elif cpu_usage > 70:
        return 5   # CPU 중간 → 5초 간격
    else:
        return 3   # CPU 낮음 → 3초 간격

# 프로세스 모니터에 적용
self.check_interval = get_adaptive_interval()
```

#### C. 메모리 압박 감지
```python
# 메모리 부족 시 캐시 자동 정리
def check_memory_pressure():
    memory = psutil.virtual_memory()
    
    if memory.percent > 90:
        # 메모리 압박 → 캐시 전체 정리
        cache.clear()
        print("⚠️ 메모리 압박 감지, 캐시 정리")
        return True
    elif memory.percent > 80:
        # 메모리 높음 → 오래된 캐시만 정리
        cache.clear_old(max_age=60)
        print("⚠️ 메모리 높음, 오래된 캐시 정리")
        return False
    
    return False
```

### 2. 우선순위 높음 (1주 내)

#### A. 배치 쓰기 (버퍼링)
```python
# 메트릭을 메모리에 버퍼링 후 배치 저장
class MetricBuffer:
    def __init__(self, flush_interval=10, max_size=1000):
        self.buffer = []
        self.flush_interval = flush_interval
        self.max_size = max_size
        self.last_flush = time.time()
    
    def add(self, metric):
        self.buffer.append(metric)
        
        # 버퍼 가득 차거나 시간 경과 시 플러시
        if len(self.buffer) >= self.max_size or \
           time.time() - self.last_flush >= self.flush_interval:
            self.flush()
    
    def flush(self):
        if not self.buffer:
            return
        
        # 배치로 한 번에 저장
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO resource_usage (program_id, cpu_percent, memory_mb) VALUES (?, ?, ?)",
            [(m['program_id'], m['cpu'], m['memory']) for m in self.buffer]
        )
        conn.commit()
        conn.close()
        
        self.buffer.clear()
        self.last_flush = time.time()
```

#### B. WAL 모드 활성화
```python
# SQLite WAL 모드 (Write-Ahead Logging)
def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # WAL 모드 활성화 (동시성 개선)
    cursor.execute("PRAGMA journal_mode = WAL")
    
    # 동기화 모드 조정 (성능 향상)
    cursor.execute("PRAGMA synchronous = NORMAL")
    
    # 캐시 크기 증가 (메모리 여유 있을 때)
    cursor.execute("PRAGMA cache_size = 10000")  # 10MB
    
    # 자동 체크포인트 (WAL 파일 크기 제한)
    cursor.execute("PRAGMA wal_autocheckpoint = 1000")
    
    conn.commit()
    conn.close()
    
    print("✅ SQLite WAL 모드 활성화 (동시성 개선)")
```

#### C. 비동기 웹훅
```python
# 웹훅을 백그라운드로 실행
from concurrent.futures import ThreadPoolExecutor
import requests

webhook_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="Webhook")

def send_webhook_async(url, data, timeout=5):
    """비동기 웹훅 발송."""
    def _send():
        try:
            response = requests.post(url, json=data, timeout=timeout)
            if response.status_code != 200:
                print(f"⚠️ 웹훅 실패: {url} (상태: {response.status_code})")
        except requests.Timeout:
            print(f"⚠️ 웹훅 타임아웃: {url}")
        except Exception as e:
            print(f"⚠️ 웹훅 오류: {url} ({str(e)})")
    
    # 백그라운드로 실행
    webhook_executor.submit(_send)
```

### 3. 우선순위 중간 (2-3주)

#### A. 게임 서버 통합
```python
# 플레이어 수 추적
class GameServerMetrics:
    def get_player_count(self, program_id):
        """게임 서버 플레이어 수 조회."""
        loader = get_plugin_loader()
        plugin = loader.get_plugin_instance(program_id, "palworld")
        
        if plugin:
            result = plugin.execute_action("get_server_info")
            return result.get("currentplayernum", 0)
        
        return None
    
    def get_resource_per_player(self, program_id):
        """플레이어당 리소스 사용량 계산."""
        stats = get_process_stats(program_id)
        player_count = self.get_player_count(program_id)
        
        if player_count and player_count > 0:
            return {
                "cpu_per_player": stats['cpu_percent'] / player_count,
                "memory_per_player": stats['memory_mb'] / player_count
            }
        
        return None
```

#### B. 이상 패턴 감지
```python
# 게임 서버 이상 패턴 감지
class AnomalyDetector:
    def __init__(self):
        self.baseline = {}  # {program_id: {cpu_avg, memory_avg}}
    
    def learn_baseline(self, program_id, metrics):
        """정상 패턴 학습 (7일 데이터)."""
        # 평균, 표준편차 계산
        cpu_values = [m['cpu_percent'] for m in metrics]
        memory_values = [m['memory_mb'] for m in metrics]
        
        self.baseline[program_id] = {
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_std': self._std(cpu_values),
            'memory_avg': sum(memory_values) / len(memory_values),
            'memory_std': self._std(memory_values)
        }
    
    def detect_anomaly(self, program_id, current_stats):
        """이상 패턴 감지 (3-sigma 규칙)."""
        if program_id not in self.baseline:
            return False
        
        baseline = self.baseline[program_id]
        
        # CPU 이상
        cpu_threshold = baseline['cpu_avg'] + (3 * baseline['cpu_std'])
        if current_stats['cpu_percent'] > cpu_threshold:
            return True, "CPU 사용량 이상"
        
        # 메모리 이상
        memory_threshold = baseline['memory_avg'] + (3 * baseline['memory_std'])
        if current_stats['memory_mb'] > memory_threshold:
            return True, "메모리 사용량 이상"
        
        return False, None
```

---

## 📋 게임 서버 환경 체크리스트

### 즉시 적용 (오늘)
```
☐ CPU 우선순위 낮추기
☐ 동적 모니터링 간격
☐ 메모리 압박 감지
☐ 웹훅 타임아웃 설정
```

### 1주 내
```
☐ 배치 쓰기 (버퍼링)
☐ WAL 모드 활성화
☐ 비동기 웹훅
☐ 비동기 플러그인
```

### 2-3주 내
```
☐ 플레이어 수 추적
☐ 이상 패턴 감지
☐ 게임 서버 통합
☐ 성능 프로파일링
```

---

## 🎯 권장 설정 (게임 서버 환경)

### 모니터링 간격
```python
# .env 설정
PROCESS_MONITOR_INTERVAL=5  # 3초 → 5초 (CPU 절약)
METRIC_COLLECTION_INTERVAL=2  # 1초 → 2초 (디스크 I/O 절약)
```

### 리소스 제한
```python
# 모니터링 시스템 리소스 제한
DB_POOL_SIZE=3  # 5개 → 3개 (메모리 절약)
JOB_QUEUE_WORKERS=1  # 2개 → 1개 (CPU 절약)
CACHE_MAX_SIZE=50MB  # 캐시 크기 제한
```

### 우선순위
```python
# 프로세스 우선순위
MONITORING_PRIORITY=BELOW_NORMAL  # 게임 서버 우선
GAME_SERVER_PRIORITY=ABOVE_NORMAL  # 게임 서버 우선순위 높임
```

---

## 🚨 위험 시나리오 및 대응

### 시나리오 1: 게임 서버 크래시
```
1. 게임 서버 크래시 발생
2. 모니터링 감지 (3-5초 내)
3. 웹훅 발송 (비동기, 5초 타임아웃)
4. 자동 재시작 (설정된 경우)
5. 플레이어 재접속

위험:
- 웹훅 블로킹 → 다른 서버 모니터링 지연
- 자동 재시작 실패 → 수동 개입 필요

대응:
✅ 비동기 웹훅
✅ 재시작 재시도 (3회)
✅ 알림 강화
```

### 시나리오 2: 메모리 부족
```
1. 게임 서버 메모리 증가
2. 시스템 메모리 90% 도달
3. 모니터링 캐시 점유
4. 게임 서버 스왑 발생
5. 심각한 성능 저하

위험:
- 게임 서버 렉 발생
- 플레이어 이탈
- 서버 다운

대응:
✅ 메모리 압박 감지
✅ 자동 캐시 정리
✅ 알림 발송
```

### 시나리오 3: 디스크 I/O 경쟁
```
1. 게임 서버 세이브 시작
2. 모니터링 메트릭 저장
3. 디스크 I/O 경쟁
4. 세이브 지연
5. 데이터 손실 위험

위험:
- 게임 진행 손실
- 플레이어 불만
- 서버 신뢰도 하락

대응:
✅ 배치 쓰기 (버퍼링)
✅ WAL 모드
✅ 쓰기 간격 조정
```

---

## 결론

```
현재 상태:
⚠️ 게임 서버와 리소스 경쟁
⚠️ 동시성 문제
⚠️ 게임 서버 특성 미고려

즉시 조치 필요:
1. CPU 우선순위 낮추기
2. 동적 모니터링 간격
3. 메모리 압박 감지
4. 웹훅 타임아웃

목표:
✅ 게임 서버 성능 최우선
✅ 모니터링 오버헤드 최소화
✅ 안정적인 공존
```

---

**작성일:** 2025-11-22  
**환경:** 단일 PC + 게임 서버  
**상태:** 완료
