import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 부모 디렉토리(백엔드)의 .env 파일 로드
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  
  // 환경 변수에서 포트 가져오기
  const vitePort = parseInt(env.VITE_PORT || '5173')
  const backendPort = env.FLASK_PORT || '8080'
  const backendUrl = `http://localhost:${backendPort}`

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: vitePort,
      proxy: {
        // Flask 백엔드 API 프록시 설정 (환경변수 사용)
        '/api': {
          target: backendUrl,
          changeOrigin: true,
          timeout: 30000,  // 30초 타임아웃
          proxyTimeout: 30000,
          ws: true,  // WebSocket 지원
        },
        '/login': {
          target: backendUrl,
          changeOrigin: true,
          timeout: 10000,
          proxyTimeout: 10000,
        },
        '/logout': {
          target: backendUrl,
          changeOrigin: true,
          timeout: 10000,
          proxyTimeout: 10000,
        },
        '/socket.io': {
          target: backendUrl,
          changeOrigin: true,
          ws: true,
          timeout: 60000,
          proxyTimeout: 60000,
        },
      },
    },
    build: {
      outDir: '../dist',
      emptyOutDir: true,
      // 번들 최적화
      rollupOptions: {
        output: {
          // 청크 분할 전략
          manualChunks: {
            // 벤더 라이브러리 분리
            'vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui': ['lucide-react'],
            'chart': ['recharts'],
            'socket': ['socket.io-client'],
          },
        },
      },
      // 번들 크기 경고 임계값
      chunkSizeWarningLimit: 500,
      // 소스맵 비활성화 (프로덕션)
      sourcemap: false,
      // 최소화 설정
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true,  // console.log 제거
        },
      },
    },
  }
})
