import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // Vite 8 (rolldown) requires manualChunks as a function
        manualChunks(id) {
          if (id.includes('node_modules/react/') || id.includes('node_modules/react-dom/')) {
            return 'vendor-react';
          }
          if (id.includes('node_modules/react-router-dom/') || id.includes('node_modules/react-router/')) {
            return 'vendor-router';
          }
          if (id.includes('node_modules/axios/')) {
            return 'vendor-axios';
          }
        },
      },
    },
    chunkSizeWarningLimit: 600,
    minify: 'oxc',
    sourcemap: false,
  },
  server: {
    port: 5173,
  },
})
