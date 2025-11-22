# API 통신 규칙 및 컨벤션

## API 응답 구조

### 기본 원칙
모든 API 응답은 일관된 구조를 따라야 합니다.

### 목록 조회 API

**규칙:** 목록 데이터는 항상 객체로 감싸서 반환합니다.

```json
{
  "key_name": [...]
}
```

**예시:**

```javascript
// ✅ 올바른 응답
GET /api/programs
{
  "programs": [
    { "id": 1, "name": "프로그램1" },
    { "id": 2, "name": "프로그램2" }
  ]
}

GET /api/plugins/available
{
  "plugins": [
    { "id": "rcon", "name": "RCON Controller" },
    { "id": "rest_api", "name": "REST API Controller" }
  ]
}

// ❌ 잘못된 응답 (배열을 직접 반환)
GET /api/programs
[
  { "id": 1, "name": "프로그램1" },
  { "id": 2, "name": "프로그램2" }
]
```

**프론트엔드 처리:**

```javascript
// 백엔드 응답이 {key: [...]} 형태일 때
const response = await axios.get('/api/programs')
const programs = response.data.programs || response.data || []

// 또는
const { programs } = response.data
```

### 단일 객체 조회 API

**규칙:** 단일 객체는 그대로 반환합니다.

```javascript
// ✅ 올바른 응답
GET /api/programs/1
{
  "id": 1,
  "name": "프로그램1",
  "path": "C:\\path\\to\\program.exe"
}
```

### 상태 조회 API

**규칙:** 상태 정보는 의미 있는 키로 감싸서 반환합니다.

```javascript
// ✅ 올바른 응답
GET /api/programs/status
{
  "programs_status": [
    {
      "id": 1,
      "running": true,
      "cpu_percent": 5.2,
      "memory_mb": 128.5
    }
  ]
}
```

### 성공/실패 응답

**규칙:** 액션 API는 성공 여부와 메시지를 포함합니다.

```javascript
// ✅ 성공 응답
POST /api/programs/1/start
{
  "success": true,
  "message": "프로그램이 실행되었습니다.",
  "pid": 12345
}

// ✅ 실패 응답
POST /api/programs/1/start
{
  "success": false,
  "message": "프로그램이 이미 실행 중입니다."
}

// ✅ 에러 응답 (4xx, 5xx)
{
  "error": "에러 메시지"
}
```

## HTTP 상태 코드

### 성공 (2xx)
- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공

### 클라이언트 에러 (4xx)
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 필요
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음

### 서버 에러 (5xx)
- `500 Internal Server Error`: 서버 오류

## API 엔드포인트 네이밍

### 규칙
1. **복수형 사용**: `/api/programs` (O), `/api/program` (X)
2. **소문자 사용**: `/api/programs` (O), `/api/Programs` (X)
3. **하이픈 사용**: `/api/program-logs` (O), `/api/program_logs` (X)
4. **동사는 마지막에**: `/api/programs/1/start` (O), `/api/start/programs/1` (X)

### 예시

```
GET    /api/programs           # 목록 조회
POST   /api/programs           # 생성
GET    /api/programs/1         # 단일 조회
PUT    /api/programs/1         # 수정
DELETE /api/programs/1/delete  # 삭제

POST   /api/programs/1/start   # 액션 (시작)
POST   /api/programs/1/stop    # 액션 (종료)
POST   /api/programs/1/restart # 액션 (재시작)

GET    /api/programs/status    # 상태 조회
GET    /api/programs/1/logs    # 로그 조회
```

## 프론트엔드 에러 처리

### 규칙
모든 API 호출은 try-catch로 감싸고 사용자에게 피드백을 제공합니다.

```javascript
// ✅ 올바른 에러 처리
const handleAction = async () => {
  try {
    const response = await axios.post('/api/programs/1/start')
    if (response.data.success) {
      // 성공 처리
      alert(response.data.message)
    } else {
      // 실패 처리
      alert(response.data.message)
    }
  } catch (error) {
    // 네트워크 에러 또는 서버 에러
    const errorMessage = error.response?.data?.error || error.message
    alert(`오류: ${errorMessage}`)
  }
}
```

## 백엔드 응답 생성

### Flask 예시

```python
from flask import jsonify

# ✅ 목록 응답
@app.route('/api/programs')
def get_programs():
    programs = get_all_programs()
    return jsonify({"programs": programs})

# ✅ 성공 응답
@app.route('/api/programs/<int:id>/start', methods=['POST'])
def start_program(id):
    success, message, pid = start_program_logic(id)
    return jsonify({
        "success": success,
        "message": message,
        "pid": pid
    })

# ✅ 에러 응답
@app.route('/api/programs/<int:id>')
def get_program(id):
    program = get_program_by_id(id)
    if not program:
        return jsonify({"error": "프로그램을 찾을 수 없습니다"}), 404
    return jsonify(program)
```

## 데이터 타입 규칙

### 날짜/시간
- **형식**: ISO 8601 (`YYYY-MM-DDTHH:mm:ss`)
- **예시**: `"2024-01-15T14:30:25"`

```javascript
// 백엔드
from datetime import datetime
timestamp = datetime.now().isoformat()

// 프론트엔드
const date = new Date(timestamp)
```

### 불리언
- **형식**: `true` / `false` (소문자)
- **예시**: `"running": true`

### 숫자
- **정수**: `"id": 1`
- **실수**: `"cpu_percent": 5.2`

### 문자열
- **빈 값**: `""` (null이 아닌 빈 문자열)
- **예시**: `"args": ""`

## 페이지네이션 (향후 적용)

### 규칙
```javascript
GET /api/programs?page=1&per_page=20

{
  "programs": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

## 필터링 (향후 적용)

### 규칙
```javascript
GET /api/programs?status=running&sort=name

{
  "programs": [...],
  "filters": {
    "status": "running",
    "sort": "name"
  }
}
```

## 체크리스트

### 새로운 API 추가 시
- [ ] API 응답 구조가 규칙을 따르는가?
- [ ] 에러 처리가 되어 있는가?
- [ ] HTTP 상태 코드가 적절한가?
- [ ] 프론트엔드에서 응답 구조를 올바르게 파싱하는가?
- [ ] README의 "API 엔드포인트" 섹션에 추가했는가?

### 디버깅 시
- [ ] 브라우저 콘솔에서 API 응답 확인
- [ ] 응답 구조가 예상과 일치하는가?
- [ ] 에러 메시지가 명확한가?

## 일반적인 실수

### 1. 배열을 직접 반환
```javascript
// ❌ 잘못된 방법
return jsonify([...])

// ✅ 올바른 방법
return jsonify({"programs": [...]})
```

### 2. 프론트엔드에서 응답 구조 무시
```javascript
// ❌ 잘못된 방법
const programs = response.data  // {programs: [...]} 객체

// ✅ 올바른 방법
const programs = response.data.programs || []
```

### 3. 에러 처리 누락
```javascript
// ❌ 잘못된 방법
const response = await axios.get('/api/programs')
setPrograms(response.data)

// ✅ 올바른 방법
try {
  const response = await axios.get('/api/programs')
  setPrograms(response.data.programs || [])
} catch (error) {
  console.error('로드 실패:', error)
  setError(error.message)
}
```

## 참고 자료

- [REST API 설계 가이드](https://restfulapi.net/)
- [HTTP 상태 코드](https://developer.mozilla.org/ko/docs/Web/HTTP/Status)
- [JSON API 스펙](https://jsonapi.org/)
