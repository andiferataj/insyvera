import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://127.0.0.1:8100' } },
  build: { chunkSizeWarningLimit: 700, rollupOptions: { output: { manualChunks(id: string) { if (id.includes('plotly.js-basic-dist-min')) return 'charts'; if (id.includes('/react-dom/') || id.includes('/react/')) return 'react-vendor'; } } } }
});
