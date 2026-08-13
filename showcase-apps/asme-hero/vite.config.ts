import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // Relative assets work both on localhost and under a GitHub Pages project path.
  base: './',
  build: {
    outDir: '../../showcase-sites/asme-hero',
    emptyOutDir: true,
  },
});
