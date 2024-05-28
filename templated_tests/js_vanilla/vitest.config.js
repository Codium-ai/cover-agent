import { defineConfig } from 'vite';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', ['cobertura', { file: 'coverage.xml' }]],
      // Add any other coverage options here
    },
  },
});
