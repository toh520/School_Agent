import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.SCHOOL_AGENT_CORE_URL ?? 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },
})
