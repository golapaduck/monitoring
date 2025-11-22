# React 프론트엔드 설정 가이드

## 📦 패키지 설치

```bash
cd frontend
npm install
```

## 🚀 개발 서버 실행

```bash
npm run dev
```

개발 서버가 `http://localhost:5173`에서 실행됩니다.

## 🔧 Flask 백엔드 연동

Vite 개발 서버는 자동으로 Flask API를 프록시합니다:
- `/api/*` → `http://localhost:8080/api/*`
- `/login` → `http://localhost:8080/login`
- `/logout` → `http://localhost:8080/logout`

### 개발 환경 실행 순서

1. **Flask 백엔드 실행** (터미널 1)
   ```bash
   cd c:\Programming\CascadeProjects\monitoring
   python app.py
   ```

2. **React 프론트엔드 실행** (터미널 2)
   ```bash
   cd c:\Programming\CascadeProjects\monitoring\frontend
   npm run dev
   ```

3. **브라우저에서 접속**
   - React 개발 서버: `http://localhost:5173`
   - Flask 백엔드: `http://localhost:8080`

## 📦 프로덕션 빌드

```bash
npm run build
```

빌드된 파일은 `../static/dist` 폴더에 생성됩니다.

## 🎨 사용된 기술 스택

- **React 19** - UI 라이브러리
- **Vite** - 빌드 도구
- **React Router** - 라우팅
- **TailwindCSS** - 스타일링
- **Lucide React** - 아이콘
- **Axios** - HTTP 클라이언트 (선택사항)

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/        # 재사용 가능한 컴포넌트
│   │   ├── ProgramCard.jsx
│   │   └── AddProgramModal.jsx
│   ├── pages/            # 페이지 컴포넌트
│   │   ├── LoginPage.jsx
│   │   └── DashboardPage.jsx
│   ├── lib/              # 유틸리티 함수
│   │   └── api.js        # API 호출 함수
│   ├── App.jsx           # 메인 앱 컴포넌트
│   ├── main.jsx          # 진입점
│   └── index.css         # 글로벌 스타일
├── public/               # 정적 파일
├── index.html            # HTML 템플릿
├── vite.config.js        # Vite 설정
├── tailwind.config.js    # TailwindCSS 설정
└── package.json          # 의존성 관리
```

## 🔑 기본 계정

- **관리자**: admin / admin
- **게스트**: guest / guest

## 🐛 문제 해결

### 포트 충돌
Vite 개발 서버 포트를 변경하려면 `vite.config.js`에서 수정:
```js
server: {
  port: 3000, // 원하는 포트로 변경
}
```

### API 프록시 오류
Flask 백엔드가 실행 중인지 확인:
```bash
curl http://localhost:8080/api/status
```

### 빌드 오류
node_modules 삭제 후 재설치:
```bash
rm -rf node_modules package-lock.json
npm install
```
