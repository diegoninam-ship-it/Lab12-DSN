import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // En desarrollo, el dev server de Vite hace de "nginx": el navegador
      // solo ve un origen, igual que en producción detrás de nginx (D9).
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
