import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // En desarrollo, /api se reenvía a FastAPI para evitar configurar CORS (ADR-04).
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
