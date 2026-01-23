import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  server: {
    port: 5174,
    host: true,
    allowedHosts: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});
