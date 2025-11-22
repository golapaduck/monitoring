# Scripts 디렉토리

> **모니터링 시스템 실행 및 배포 스크립트**

---

## 📋 스크립트 목록

### 1. `dev.bat` - 개발 모드

**목적:** 개발 중에 프론트엔드와 백엔드를 동시에 실행

**사용 방법:**
```bash
scripts\dev.bat
```

**동작:**
```
1. 백엔드 시작 (새 창)
   - Flask 개발 서버
   - 포트: 8080
   - 자동 리로드 활성화

2. 프론트엔드 시작 (새 창)
   - Vite 개발 서버
   - 포트: 5173
   - Hot Module Replacement (HMR)

3. 브라우저 접속
   - http://localhost:5173
```

**특징:**
```
✅ 두 개의 새 창에서 실행
✅ 자동 리로드 (코드 변경 시)
✅ 디버그 모드 활성화
✅ 상세한 로그 출력
```

---

### 2. `prod.bat` - 프로덕션 모드

**목적:** 프로덕션 환경에서 최적화된 모드로 실행

**사용 방법:**
```bash
scripts\prod.bat
```

**동작:**
```
1. 환경 변수 설정
   - PRODUCTION=True
   - FLASK_ENV=production

2. 프론트엔드 빌드 확인
   - dist 폴더 확인
   - 없으면 자동 빌드

3. 백엔드 시작
   - Waitress WSGI 서버
   - 포트: 8080
   - 멀티스레드 지원

4. 브라우저 접속
   - http://localhost:8080
```

**특징:**
```
✅ 최적화된 성능
✅ 프론트엔드 정적 파일 서빙
✅ 프로덕션 로깅
✅ 자동 빌드 (필요시)
```

---

### 3. `deploy.bat` - 배포 자동화

**목적:** 배포 전 필요한 모든 작업을 자동으로 수행

**사용 방법:**
```bash
scripts\deploy.bat
```

**동작:**
```
1. 프론트엔드 빌드
   - npm run build
   - dist 폴더 생성

2. 백엔드 의존성 설치
   - pip install -r requirements.txt
   - 필요한 패키지 설치

3. 환경 변수 확인
   - .env 파일 확인
   - 없으면 자동 생성

4. 배포 완료
   - prod.bat 실행 준비
```

**특징:**
```
✅ 자동화된 배포
✅ 에러 처리
✅ 환경 변수 자동 생성
✅ 단계별 진행 상황 표시
```

---

### 4. `check-performance.bat` - 성능 확인

**목적:** 시스템 성능 및 API 응답 시간 확인

**사용 방법:**
```bash
scripts\check-performance.bat
```

**확인 항목:**
```
1. 시스템 정보
   - OS, 메모리, CPU

2. CPU 정보
   - 코어 수, 논리 프로세서

3. 메모리 사용량
   - 사용 중, 여유, 사용률

4. Python 프로세스
   - 실행 여부

5. 포트 확인
   - 8080 포트 사용 여부

6. API 응답 시간
   - http://localhost:8080/api/programs

7. 권장 설정
   - 환경 요구사항
   - 최적화 설정
```

---

## 🚀 **빠른 시작**

### **개발 시작**
```bash
scripts\dev.bat
```

### **프로덕션 배포**
```bash
scripts\deploy.bat
scripts\prod.bat
```

### **성능 확인**
```bash
scripts\check-performance.bat
```

---

## 📊 **스크립트 비교**

| 스크립트 | 목적 | 환경 | 포트 | 자동 리로드 |
|---------|------|------|------|----------|
| `dev.bat` | 개발 | 개발 | 5173 + 8080 | ✅ |
| `prod.bat` | 운영 | 프로덕션 | 8080 | ❌ |
| `deploy.bat` | 배포 | 배포 | - | - |
| `check-performance.bat` | 모니터링 | 모니터링 | - | - |

---

## 🔧 **환경 변수**

### `dev.bat`
```
PRODUCTION=False
FLASK_ENV=development
FLASK_DEBUG=True
```

### `prod.bat`
```
PRODUCTION=True
FLASK_ENV=production
```

---

## 📝 **사용 예시**

### **개발 중**
```bash
# 1. 개발 서버 시작
scripts\dev.bat

# 2. 브라우저에서 http://localhost:5173 접속
# 3. 코드 수정 시 자동 리로드
```

### **배포 전**
```bash
# 1. 배포 자동화 실행
scripts\deploy.bat

# 2. .env 파일 확인 및 수정
# 3. 프로덕션 시작
scripts\prod.bat
```

### **성능 확인**
```bash
# 1. 성능 확인 스크립트 실행
scripts\check-performance.bat

# 2. 시스템 리소스 확인
# 3. API 응답 시간 확인
```

---

## ⚠️ **주의사항**

### `dev.bat` 사용 시
```
❌ 프로덕션 환경에서 사용 금지
❌ 성능이 낮음
❌ 보안 설정 없음
```

### `prod.bat` 사용 시
```
✅ 프로덕션 환경에서만 사용
✅ 최적화된 성능
✅ 보안 설정 포함
```

### `deploy.bat` 사용 시
```
⚠️ 프론트엔드 빌드 시간 소요 (1-2분)
⚠️ 인터넷 연결 필요 (npm 패키지 다운로드)
⚠️ 관리자 권한 권장
```

---

## 🐛 **문제 해결**

### 스크립트가 실행되지 않음
```
1. 관리자 권한으로 명령 프롬프트 실행
2. 스크립트 다시 실행
```

### Python이 없다는 오류
```
1. Python 설치 확인
2. PATH 환경 변수 확인
3. where python 명령으로 경로 확인
```

### npm이 없다는 오류
```
1. Node.js 설치 확인
2. PATH 환경 변수 확인
3. where npm 명령으로 경로 확인
```

### 포트 충돌
```
1. netstat -ano | findstr :8080 (포트 확인)
2. 기존 프로세스 종료
3. 스크립트 다시 실행
```

---

## 📚 **다음 단계**

### 1. 개발 시작
```bash
scripts\dev.bat
```

### 2. 배포 준비
```bash
scripts\deploy.bat
```

### 3. 프로덕션 실행
```bash
scripts\prod.bat
```

### 4. 작업 스케줄러 설정
```
doc/WINDOWS_SCHEDULER_GUIDE.md 참고
```

---

**작성일:** 2025-11-22  
**버전:** 1.0  
**상태:** 완료
