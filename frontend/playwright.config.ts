import { defineConfig, devices } from '@playwright/test';

const TEST_TIMEOUT_MS = 30_000;
const SERVER_TIMEOUT_MS = 60_000;
export default defineConfig({
  testDir: './e2e',
  timeout: TEST_TIMEOUT_MS,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH }
      : undefined,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI && process.env.E2E_REAL_API !== 'true',
    timeout: SERVER_TIMEOUT_MS,
  },
});
