import { loadEnv } from 'vite';
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import type { Plugin } from 'vite';
import { DEFAULT_IMAGE_MAX_BYTES, DEFAULT_AUDIO_MAX_BYTES } from './src/app/constants.ts';

const DEFAULT_PORT = 5173;

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxy = {
    '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:8000', changeOrigin: true },
  };
  return {
    plugins: [react(), runtime_config(env)],
    server: {
      host: env.FRONTEND_HOST || '127.0.0.1',
      port: Number(env.FRONTEND_PORT || DEFAULT_PORT),
      strictPort: true,
      proxy,
    },
    preview: { proxy },
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test_setup.ts'],
      include: ['src/**/*.test.{ts,tsx}'],
      clearMocks: true,
    },
  };
});

function runtime_config(env: Record<string, string>): Plugin {
  const limits = {
    image_max_bytes: Number(env.IMAGE_MAX_BYTES || DEFAULT_IMAGE_MAX_BYTES),
    audio_max_bytes: Number(env.AUDIO_MAX_BYTES || DEFAULT_AUDIO_MAX_BYTES),
  };
  if (!Object.values(limits).every((value) => Number.isSafeInteger(value) && value > 0))
    throw new Error('Upload limits must be positive integers');
  return {
    name: 'runtime-upload-limits',
    configureServer(server) {
      server.middlewares.use('/config.json', (_request, response) => {
        response.setHeader('Content-Type', 'application/json');
        response.setHeader('Cache-Control', 'no-store');
        response.end(JSON.stringify(limits));
      });
    },
    configurePreviewServer(server) {
      server.middlewares.use('/config.json', (_request, response) => {
        response.setHeader('Content-Type', 'application/json');
        response.setHeader('Cache-Control', 'no-store');
        response.end(JSON.stringify(limits));
      });
    },
  };
}
