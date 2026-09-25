import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // When the FastAPI backend is ready, forward /api calls to it during development
    // and leave VITE_API_URL empty in .env:
    // proxy: { '/api': 'http://localhost:8000' },
  },
});
