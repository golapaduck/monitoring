# 리팩토링 Phase 2 - 추가 개선사항

## 🔍 발견된 문제점

### 1. **코드 중복 및 구조 문제**

#### ❌ 문제: API 엔드포인트 인증 중복
```python
# 모든 API에서 반복
if "user" not in session:
    return jsonify({"error": "Unauthorized"}), 401
```

**해결책: 데코레이터 패턴**
```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@programs_api.route("", methods=["GET"])
@require_auth
def programs():
    # 인증 코드 제거
    programs = get_all_programs()
    return jsonify({"programs": programs})
```

---

#### ❌ 문제: Admin 권한 체크 중복
```python
# 여러 곳에서 반복
if session.get("role") != "admin":
    return jsonify({"error": "Forbidden"}), 403
```

**해결책: 권한 데코레이터**
```python
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated_function

@programs_api.route("", methods=["POST"])
@require_auth
@require_admin
def add_program():
    # 권한 체크 코드 제거
    ...
```

---

#### ❌ 문제: 에러 응답 형식 불일치
```python
# 다양한 형식
return jsonify({"error": "..."}), 400
return jsonify({"success": False, "message": "..."}), 400
return {"error": "..."}, 400
```

**해결책: 표준 응답 헬퍼**
```python
def success_response(data=None, message=None, status=200):
    response = {"success": True}
    if message:
        response["message"] = message
    if data:
        response["data"] = data
    return jsonify(response), status

def error_response(message, status=400, error_code=None):
    response = {
        "success": False,
        "error": message
    }
    if error_code:
        response["error_code"] = error_code
    return jsonify(response), status
```

---

### 2. **타입 힌트 부족**

#### ❌ 현재 상태
```python
def get_process_status(program_path, pid=None):
    ...

def start_program(program_path, args=""):
    ...
```

#### ✅ 개선안
```python
from typing import Optional, Tuple, List, Dict, Any

def get_process_status(
    program_path: str, 
    pid: Optional[int] = None
) -> Tuple[bool, Optional[int]]:
    """프로그램 경로로 프로세스 실행 여부 확인.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        pid: 프로세스 ID (선택사항)
        
    Returns:
        (실행 여부, 현재 PID 또는 None)
    """
    ...

def start_program(
    program_path: str, 
    args: str = ""
) -> Tuple[bool, str, Optional[int]]:
    """프로그램 실행.
    
    Args:
        program_path: 프로그램 실행 파일 경로
        args: 실행 인자
        
    Returns:
        (성공 여부, 메시지, PID 또는 None)
    """
    ...
```

---

### 3. **설정 관리 분산**

#### ❌ 문제: 설정이 여러 곳에 분산
- `config.py`
- `.env`
- 하드코딩된 값들

#### ✅ 해결책: Pydantic Settings
```python
# config/settings.py
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    """애플리케이션 설정 (환경 변수 + 기본값)"""
    
    # Flask
    flask_host: str = Field(default="0.0.0.0", env="FLASK_HOST")
    flask_port: int = Field(default=8080, env="FLASK_PORT")
    flask_debug: bool = Field(default=False, env="FLASK_DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Database
    database_path: str = Field(default="data/monitoring.db", env="DATABASE_PATH")
    
    # Session
    session_lifetime: int = Field(default=3600, env="SESSION_LIFETIME")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_max_bytes: int = Field(default=10485760, env="LOG_MAX_BYTES")
    
    # Waitress
    waitress_threads: Optional[int] = Field(default=None, env="WAITRESS_THREADS")
    waitress_connection_limit: int = Field(default=100, env="WAITRESS_CONNECTION_LIMIT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

### 4. **에러 처리 표준화**

#### ❌ 현재: 일관성 없는 에러 처리
```python
try:
    ...
except Exception as e:
    print(f"오류: {str(e)}")
    return False

try:
    ...
except Exception:
    pass

try:
    ...
except Exception as e:
    return jsonify({"error": str(e)}), 500
```

#### ✅ 개선: 커스텀 예외 + 핸들러
```python
# exceptions.py
class MonitoringError(Exception):
    """기본 예외"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ProcessNotFoundError(MonitoringError):
    """프로세스를 찾을 수 없음"""
    def __init__(self, process_name: str):
        super().__init__(
            f"프로세스를 찾을 수 없습니다: {process_name}",
            status_code=404
        )

class PluginLoadError(MonitoringError):
    """플러그인 로드 실패"""
    def __init__(self, plugin_name: str, reason: str):
        super().__init__(
            f"플러그인 로드 실패: {plugin_name} - {reason}",
            status_code=500
        )

# app.py
@app.errorhandler(MonitoringError)
def handle_monitoring_error(error):
    return jsonify({
        "success": False,
        "error": error.message
    }), error.status_code
```

---

### 5. **로깅 시스템 비표준화**

#### ❌ 현재: print() 사용
```python
print(f"✅ [Programs API] 프로그램 등록: {name}")
print(f"⚠️ [Process Manager] 오류: {str(e)}")
```

#### ✅ 개선: 표준 logging 모듈
```python
# utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """표준화된 로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# 사용
logger = setup_logger(__name__, 'logs/programs.log')
logger.info(f"프로그램 등록: {name}")
logger.warning(f"프로세스 오류: {str(e)}")
```

---

### 6. **데이터베이스 쿼리 최적화**

#### ❌ 문제: N+1 쿼리
```python
# 각 프로그램마다 별도 쿼리
for program in programs:
    is_running, pid = get_process_status(program["path"], program.get("pid"))
```

#### ✅ 개선: 배치 처리
```python
def get_programs_status_batch(programs: List[Dict]) -> List[Dict]:
    """여러 프로그램 상태를 한 번에 조회"""
    # psutil.process_iter() 한 번만 호출
    running_processes = {
        proc.info['name'].lower(): proc.info['pid']
        for proc in psutil.process_iter(['name', 'pid'])
    }
    
    result = []
    for program in programs:
        program_name = Path(program['path']).name.lower()
        pid = running_processes.get(program_name)
        result.append({
            **program,
            'running': pid is not None,
            'pid': pid
        })
    
    return result
```

---

### 7. **프론트엔드 개선**

#### ❌ 문제: Props Drilling
```jsx
// App → DashboardPage → ProgramCard → ...
<DashboardPage user={user} onLogout={onLogout} />
```

#### ✅ 해결: Context API
```jsx
// contexts/AuthContext.jsx
import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  
  const login = (userData) => setUser(userData)
  const logout = () => setUser(null)
  
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

// 사용
function DashboardPage() {
  const { user, logout } = useAuth()
  // props 전달 불필요
}
```

---

#### ❌ 문제: API 호출 중복
```jsx
// 여러 컴포넌트에서 axios 직접 호출
const response = await axios.get('/api/programs')
```

#### ✅ 해결: API 서비스 레이어
```javascript
// services/api.js
class ApiService {
  constructor(baseURL) {
    this.client = axios.create({ baseURL })
  }
  
  async get(url) {
    try {
      const response = await this.client.get(url)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }
  
  handleError(error) {
    if (error.response) {
      return new Error(error.response.data.error || '서버 오류')
    }
    return new Error('네트워크 오류')
  }
}

export const api = new ApiService('/api')
```

---

### 8. **TODO 항목 구현**

#### 📝 api/status.py
```python
# TODO: psutil을 사용해서 시스템 리소스 정보 수집
@status_api.route("/system", methods=["GET"])
def get_system_status():
    """시스템 리소스 상태 조회"""
    import psutil
    
    return jsonify({
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "network": {
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv
        }
    })
```

---

## 📋 우선순위별 작업 목록

### 🔴 High Priority (즉시)
1. ✅ **인증 데코레이터 추가**
   - `@require_auth`
   - `@require_admin`
   - 코드 중복 제거

2. ✅ **표준 응답 헬퍼**
   - `success_response()`
   - `error_response()`
   - 일관된 API 응답

3. ✅ **타입 힌트 추가**
   - 모든 함수에 타입 힌트
   - mypy 검증

4. ✅ **커스텀 예외 클래스**
   - `MonitoringError`
   - `ProcessNotFoundError`
   - `PluginLoadError`

### 🟡 Medium Priority (1-2주)
5. ✅ **로깅 시스템 통합**
   - print() → logging
   - 파일 로깅
   - 로그 레벨 관리

6. ✅ **Pydantic Settings**
   - 설정 통합
   - 환경 변수 검증
   - 타입 안전성

7. ✅ **데이터베이스 최적화**
   - N+1 쿼리 제거
   - 배치 처리
   - 인덱스 추가

8. ✅ **프론트엔드 Context API**
   - Props drilling 제거
   - 전역 상태 관리

### 🟢 Low Priority (장기)
9. ✅ **API 서비스 레이어**
   - axios 래핑
   - 에러 처리 통합

10. ✅ **TODO 항목 구현**
    - 시스템 리소스 API
    - 기타 미완성 기능

---

## 🎯 예상 효과

### 코드 품질
- ✅ 중복 코드 50% 감소
- ✅ 타입 안전성 향상
- ✅ 유지보수성 향상

### 성능
- ✅ N+1 쿼리 제거로 30% 속도 향상
- ✅ 배치 처리로 메모리 효율 증가

### 개발 경험
- ✅ 일관된 코드 스타일
- ✅ 명확한 에러 메시지
- ✅ 자동 완성 지원 (타입 힌트)

---

## 📅 실행 계획

### Week 1: 기본 인프라
- [ ] 인증/권한 데코레이터
- [ ] 표준 응답 헬퍼
- [ ] 커스텀 예외 클래스

### Week 2: 타입 안전성
- [ ] 타입 힌트 추가
- [ ] Pydantic Settings
- [ ] mypy 설정

### Week 3: 로깅 및 최적화
- [ ] 로깅 시스템 통합
- [ ] 데이터베이스 최적화
- [ ] 성능 테스트

### Week 4: 프론트엔드
- [ ] Context API
- [ ] API 서비스 레이어
- [ ] 컴포넌트 리팩토링

---

## 🔧 즉시 시작 가능한 작업

다음 중 어떤 작업부터 시작하시겠어요?

1. **인증 데코레이터** (30분)
2. **표준 응답 헬퍼** (20분)
3. **타입 힌트 추가** (1시간)
4. **커스텀 예외 클래스** (30분)
5. **로깅 시스템 통합** (1시간)
