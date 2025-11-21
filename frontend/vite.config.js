import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 부모 디렉토리(백엔드)의 .env 파일 로드
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  const backendPort = env.FLASK_PORT || '5000'
  const backendUrl = `http://localhost:${backendPort}`

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        // Flask 백엔드 API 프록시 설정 (환경변수 사용)
        '/api': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/login': {
          target: backendUrl,
          changeOrigin: true,
        },
        '/logout': {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: '../static/dist',
      emptyOutDir: true,
    },
  }
})
