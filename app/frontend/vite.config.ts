import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(), // Plugin oficial de la Versión 4
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:9002',
        changeOrigin: true,
      }
    }
  }
})