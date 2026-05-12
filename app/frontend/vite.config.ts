import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    // BLINDAJE ESPECÍFICO PARA NGROK:
    // Aunque 'all' funciona en teoría, Vite prefiere la ruta exacta para mayor seguridad.
    // Hemos añadido la URL que te asignó Ngrok hoy.
    allowedHosts: [
      'showroom-maybe-giddiness.ngrok-free.dev',
      'localhost',
      '.ngrok-free.app', // Esto permite cualquier subdominio de ngrok como respaldo
      '.ngrok-free.dev'  // Esto permite tu dirección actual
    ],

    proxy: {
      '/api': {
        target: 'http://localhost:9002',
        changeOrigin: true,
      }
    }
  }
})