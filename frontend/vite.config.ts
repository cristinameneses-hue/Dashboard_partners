import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Backend FastAPI (Dashboard) - puerto 8000
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Backend Flask (Luda Mind) health check - puerto 5000
      '/luda-health': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/luda-health/, '/health'),
      },
      // Backend Flask (Luda Mind) API - puerto 5000
      '/luda-api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/luda-api/, '/api'),
      },
    },
  },
})


