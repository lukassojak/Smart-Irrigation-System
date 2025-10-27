import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // every request starting with /api will be forwarded to the backend server
      '/api': 'http://localhost:8000',
    },
  },
})
