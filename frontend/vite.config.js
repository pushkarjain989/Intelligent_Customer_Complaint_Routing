import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/predict': 'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
      '/train': 'http://127.0.0.1:8000',
      '/visualize': 'http://127.0.0.1:8000',
      '/status': 'http://127.0.0.1:8000',
      '/presets': 'http://127.0.0.1:8000',
      '/clusters': 'http://127.0.0.1:8000',
      '/batch_predict': 'http://127.0.0.1:8000',
    }
  }
})
