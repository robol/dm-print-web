import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/userinfo': 'http://localhost:5000',
      '/login': 'http://localhost:5000',
      '/logout': 'http://localhost:5000',
      '/getPrinters': 'http://localhost:5000',
      '/printFile': 'http://localhost:5000',
    },
  },
  build: {
    outDir: 'build',
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
  },
});
