# 프로젝트 리팩토링 계획

## 📊 현재 상태 분석

### 🔴 주요 문제점

#### 1. **구조적 문제**
- ❌ 루트 디렉토리에 불필요한 `node_modules` 존재
- ❌ 루트에 `serve.py` 중복 (backend/serve.py와 중복)
- ❌ `__pycache__` 파일이 Git에 포함됨
- ❌ `.gitignore` 설정 부족

#### 2. **코드 품질 문제**
- ❌ 일부 함수가 너무 길고 복잡함
- ❌ 에러 처리가 일관되지 않음
- ❌ 로깅 시스템이 표준화되지 않음
- ❌ 타입 힌트 부족 (Python)

#### 3. **의존성 관리**
- ❌ 루트에 불필요한 `package.json` 존재
- ❌ 프론트엔드/백엔드 의존성 혼재

#### 4. **설정 파일 문제**
- ❌ 환경 변수 관리 개선 필요
- ❌ 설정 파일 분산 (config.py, .env, 등)

#### 5. **테스트 부재**
- ❌ 단위 테스트 없음
- ❌ 통합 테스트 없음
- ❌ E2E 테스트 없음

---

## 🎯 리팩토링 목표

### Phase 1: 프로젝트 구조 정리 (우선순위: 높음)
1. ✅ 불필요한 파일/폴더 제거
2. ✅ `.gitignore` 개선
3. ✅ 디렉토리 구조 최적화
4. ✅ 문서 정리

### Phase 2: 코드 품질 개선 (우선순위: 높음)
1. ✅ 타입 힌트 추가 (Python)
2. ✅ 에러 처리 표준화
3. ✅ 로깅 시스템 통합
4. ✅ 함수 분리 및 단순화

### Phase 3: 아키텍처 개선 (우선순위: 중간)
1. ✅ 설정 관리 통합
2. ✅ 의존성 주입 패턴 적용
3. ✅ 레이어 분리 명확화
4. ✅ 인터페이스 정의

### Phase 4: 테스트 추가 (우선순위: 중간)
1. ✅ 단위 테스트 프레임워크 설정
2. ✅ 핵심 기능 테스트 작성
3. ✅ CI/CD 파이프라인 구축

### Phase 5: 성능 최적화 (우선순위: 낮음)
1. ✅ 데이터베이스 쿼리 최적화
2. ✅ 캐싱 전략 도입
3. ✅ 프론트엔드 번들 최적화

---

## 📁 제안하는 새로운 구조

```
monitoring/
├── backend/
│   ├── src/                      # 소스 코드
│   │   ├── api/                  # API 엔드포인트
│   │   ├── core/                 # 핵심 비즈니스 로직
│   │   │   ├── process/          # 프로세스 관리
│   │   │   ├── monitoring/       # 모니터링
│   │   │   └── plugins/          # 플러그인 시스템
│   │   ├── models/               # 데이터 모델
│   │   ├── services/             # 비즈니스 서비스
│   │   ├── utils/                # 유틸리티
│   │   └── config/               # 설정
│   ├── tests/                    # 테스트
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   ├── logs/                     # 로그 (gitignore)
│   ├── data/                     # 데이터 (gitignore)
│   ├── requirements.txt
│   ├── requirements-dev.txt      # 개발 의존성
│   └── app.py                    # 진입점
│
├── frontend/
│   ├── src/
│   │   ├── components/           # 재사용 컴포넌트
│   │   ├── pages/                # 페이지
│   │   ├── hooks/                # 커스텀 훅
│   │   ├── services/             # API 서비스
│   │   ├── utils/                # 유틸리티
│   │   ├── contexts/             # React Context
│   │   └── types/                # TypeScript 타입
│   ├── public/
│   ├── tests/                    # 테스트
│   └── package.json
│
├── docs/                         # 문서
│   ├── api/                      # API 문서
│   ├── architecture/             # 아키텍처 문서
│   └── guides/                   # 가이드
│
├── scripts/                      # 실행 스크립트
│   ├── dev.bat
│   ├── prod.bat
│   ├── backup.bat
│   └── README.md
│
├── .github/                      # GitHub 설정
│   └── workflows/                # CI/CD
│
├── .gitignore
├── .env.example
├── README.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

---

## 🔧 구체적인 리팩토링 작업

### 1. 즉시 처리 (Phase 1)

#### 1.1 불필요한 파일 제거
```bash
# 삭제 대상
- /node_modules/          # 루트의 불필요한 node_modules
- /package.json           # 루트의 불필요한 package.json
- /package-lock.json      # 루트의 불필요한 package-lock.json
- /serve.py               # 중복 파일 (backend/serve.py 사용)
- /__pycache__/           # Python 캐시
- /backend/__pycache__/   # Python 캐시
```

#### 1.2 .gitignore 개선
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# 환경 변수
.env
.env.local
.env.backup

# 데이터
backend/data/*.db
backend/data/*.json
!backend/data/.gitkeep

# 로그
backend/logs/*.log
backend/logs/*.gz
!backend/logs/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# 빌드
frontend/dist/
frontend/build/

# 백업
*.backup
.env.backup
```

#### 1.3 문서 구조 개선
```
doc/ → docs/
├── api-conventions.md → api/conventions.md
├── plan.md → project/plan.md
└── README.md → guides/getting-started.md
```

---

### 2. 코드 품질 개선 (Phase 2)

#### 2.1 타입 힌트 추가
```python
# Before
def get_process_status(program_path, pid=None):
    ...

# After
from typing import Optional, Tuple

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
```

#### 2.2 에러 처리 표준화
```python
# 커스텀 예외 클래스
class MonitoringError(Exception):
    """모니터링 시스템 기본 예외"""
    pass

class ProcessNotFoundError(MonitoringError):
    """프로세스를 찾을 수 없음"""
    pass

class PluginLoadError(MonitoringError):
    """플러그인 로드 실패"""
    pass
```

#### 2.3 로깅 시스템 통합
```python
# utils/logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str) -> logging.Logger:
    """표준화된 로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러
    handler = RotatingFileHandler(
        f'logs/{name}.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

---

### 3. 아키텍처 개선 (Phase 3)

#### 3.1 설정 관리 통합
```python
# config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Flask
    flask_host: str = "0.0.0.0"
    flask_port: int = 8080
    flask_debug: bool = False
    secret_key: str
    
    # Database
    database_url: str = "sqlite:///data/monitoring.db"
    
    # Logging
    log_level: str = "INFO"
    log_max_bytes: int = 10485760
    log_backup_count: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

#### 3.2 의존성 주입
```python
# core/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    """의존성 주입 컨테이너"""
    
    config = providers.Configuration()
    
    # Database
    database = providers.Singleton(Database, config.database_url)
    
    # Services
    process_service = providers.Factory(
        ProcessService,
        database=database
    )
    
    monitoring_service = providers.Factory(
        MonitoringService,
        process_service=process_service
    )
```

---

### 4. 테스트 추가 (Phase 4)

#### 4.1 테스트 구조
```
backend/tests/
├── unit/
│   ├── test_process_manager.py
│   ├── test_database.py
│   └── test_plugins.py
├── integration/
│   ├── test_api.py
│   └── test_websocket.py
├── fixtures/
│   └── sample_data.py
└── conftest.py
```

#### 4.2 예시 테스트
```python
# tests/unit/test_process_manager.py
import pytest
from src.core.process.manager import ProcessManager

class TestProcessManager:
    def test_get_process_status_running(self):
        """실행 중인 프로세스 상태 확인"""
        manager = ProcessManager()
        is_running, pid = manager.get_status("notepad.exe")
        assert isinstance(is_running, bool)
        assert isinstance(pid, (int, type(None)))
    
    def test_get_process_status_not_running(self):
        """실행되지 않은 프로세스 상태 확인"""
        manager = ProcessManager()
        is_running, pid = manager.get_status("nonexistent.exe")
        assert is_running is False
        assert pid is None
```

---

## 📋 실행 계획

### Week 1: 프로젝트 구조 정리
- [ ] 불필요한 파일 제거
- [ ] .gitignore 개선
- [ ] 문서 구조 재정리
- [ ] README 업데이트

### Week 2: 코드 품질 개선
- [ ] 타입 힌트 추가
- [ ] 에러 처리 표준화
- [ ] 로깅 시스템 통합
- [ ] 코드 리뷰 및 정리

### Week 3: 아키텍처 개선
- [ ] 설정 관리 통합
- [ ] 의존성 주입 도입
- [ ] 레이어 분리
- [ ] 리팩토링 검증

### Week 4: 테스트 및 문서화
- [ ] 테스트 프레임워크 설정
- [ ] 핵심 기능 테스트 작성
- [ ] API 문서 작성
- [ ] 배포 가이드 작성

---

## 🎯 우선순위별 작업

### 🔴 High Priority (즉시 처리)
1. 불필요한 파일 제거
2. .gitignore 개선
3. 타입 힌트 추가
4. 에러 처리 표준화

### 🟡 Medium Priority (1-2주 내)
1. 로깅 시스템 통합
2. 설정 관리 개선
3. 테스트 추가
4. 문서 정리

### 🟢 Low Priority (장기)
1. 의존성 주입
2. 성능 최적화
3. CI/CD 구축
4. 모니터링 대시보드 개선

---

## 💡 리팩토링 원칙

1. **점진적 개선**: 한 번에 모든 것을 바꾸지 않음
2. **하위 호환성**: 기존 기능 유지
3. **테스트 우선**: 리팩토링 전 테스트 작성
4. **문서화**: 변경사항 문서화
5. **코드 리뷰**: 팀원과 리뷰

---

## 📊 성공 지표

- [ ] 코드 커버리지 > 80%
- [ ] 타입 힌트 커버리지 > 90%
- [ ] 린트 에러 0개
- [ ] 문서화 완료율 100%
- [ ] 빌드 시간 < 30초
- [ ] 테스트 실행 시간 < 10초

---

## 🔗 참고 자료

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Flask Best Practices](https://flask.palletsprojects.com/en/2.3.x/patterns/)
- [React Best Practices](https://react.dev/learn/thinking-in-react)
- [Clean Code](https://github.com/ryanmcdermott/clean-code-javascript)
