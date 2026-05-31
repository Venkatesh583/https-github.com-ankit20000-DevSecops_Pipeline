import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api/users': { target: 'http://localhost:5001', changeOrigin: true, rewrite: (p) => p.replace(/^\/api\/users/, '') },
      '/api/appointments': { target: 'http://localhost:5002', changeOrigin: true, rewrite: (p) => p.replace(/^\/api\/appointments/, '') },
      '/api/reports': { target: 'http://localhost:5003', changeOrigin: true, rewrite: (p) => p.replace(/^\/api\/reports/, '') },
    },
  },
  build: {
    outDir: 'build',
  },
});
