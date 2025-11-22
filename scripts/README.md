# 실행 스크립트 가이드

## 📁 스크립트 구조

```
monitoring/
├── dev.bat              # 개발 모드 래퍼
├── prod.bat             # 프로덕션 모드 래퍼
└── scripts/
    ├── dev.bat          # 개발 모드 실제 스크립트
    └── prod.bat         # 프로덕션 모드 실제 스크립트
```

---

## 🔧 개발 모드 (dev.bat)

### 백엔드만 실행 (기본)
```bash
dev.bat
```

**실행 내용:**
- `.env` 파일을 개발 모드로 설정 (`PRODUCTION=False`)
- Flask 백엔드 서버 실행 (http://localhost:8080)
- 프론트엔드는 별도 실행 필요

**사용 시나리오:**
- 백엔드 개발 중
- 프론트엔드는 별도 터미널에서 실행

---

### 백엔드 + 프론트엔드 통합 실행
```bash
dev.bat full
```

**실행 내용:**
- `.env` 파일을 개발 모드로 설정
- 백엔드 서버 실행 (새 터미널)
- 프론트엔드 서버 실행 (새 터미널)

**사용 시나리오:**
- 전체 개발 환경 빠른 시작
- 두 서버 동시 실행 필요

---

## 🚀 프로덕션 모드 (prod.bat)

### 빌드 + 배포 (기본)
```bash
prod.bat
```

**실행 내용:**
1. 프론트엔드 빌드 (`npm run build`)
2. `.env` 파일을 프로덕션 모드로 설정 (`PRODUCTION=True`)
3. 통합 서버 실행 (http://localhost:8080)
4. 종료 시 `.env` 파일 복원

**사용 시나리오:**
- 프로덕션 배포
- 빌드부터 실행까지 한 번에

---

### 빌드만
```bash
prod.bat build
```

**실행 내용:**
- 프론트엔드만 빌드 (`npm run build`)
- `frontend/dist` 폴더 생성

**사용 시나리오:**
- 빌드 파일만 생성
- 실행은 나중에

---

### 실행만
```bash
prod.bat run
```

**실행 내용:**
- 빌드 파일 존재 여부 확인
- `.env` 파일을 프로덕션 모드로 설정
- 통합 서버 실행
- 종료 시 `.env` 파일 복원

**사용 시나리오:**
- 이미 빌드된 상태
- 서버만 재시작

---

## 📊 스크립트 비교표

| 명령어 | 모드 | 빌드 | 백엔드 | 프론트엔드 | .env 설정 |
|--------|------|------|--------|------------|-----------|
| `dev.bat` | 개발 | ❌ | ✅ | ❌ | PRODUCTION=False |
| `dev.bat full` | 개발 | ❌ | ✅ | ✅ | PRODUCTION=False |
| `prod.bat` | 프로덕션 | ✅ | ✅ | 빌드됨 | PRODUCTION=True |
| `prod.bat build` | 프로덕션 | ✅ | ❌ | ❌ | 변경 없음 |
| `prod.bat run` | 프로덕션 | ❌ | ✅ | 빌드됨 | PRODUCTION=True |

---

## 🗑️ 삭제된 구 스크립트

다음 스크립트들은 통합되어 더 이상 사용하지 않습니다:

- ~~`start.bat`~~ → `dev.bat full`
- ~~`run-dev.bat`~~ → `dev.bat`
- ~~`build.bat`~~ → `prod.bat build`
- ~~`run-production.bat`~~ → `prod.bat run`
- ~~`deploy.bat`~~ → `prod.bat`

---

## 💡 팁

### 개발 시작
```bash
# 빠른 시작
dev.bat full

# 또는 백엔드만
dev.bat
cd frontend && npm run dev  # 별도 터미널
```

### 프로덕션 배포
```bash
# 한 번에
prod.bat

# 또는 단계별
prod.bat build
prod.bat run
```

### .env 파일 관리
- 스크립트가 자동으로 관리하므로 수동 수정 불필요
- 프로덕션 종료 시 자동으로 개발 모드로 복원
