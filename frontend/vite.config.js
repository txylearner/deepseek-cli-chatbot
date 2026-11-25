import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 开发期把接口请求转发到 FastAPI（backend 在 8000 端口）
    proxy: {
      '/chat': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/sessions': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/study': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
