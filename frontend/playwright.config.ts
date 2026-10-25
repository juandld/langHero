import { defineConfig, devices } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SPEAK_FIXTURE_WAV = path.join(__dirname, 'tests', 'fixtures', 'learner-sample.wav');

export default defineConfig({
  testDir: './tests',
  globalSetup: './tests/global-setup.ts',
  globalTeardown: './tests/global-teardown.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['list']],

  use: {
    baseURL: 'http://localhost:5200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    // Grant mic to every test; speak-loop.spec.ts actually uses it, others
    // are unaffected.
    permissions: ['microphone'],
    launchOptions: {
      // Chrome flags for synthetic microphone input — reads from a WAV file
      // instead of hardware. Lets speak-loop.spec.ts drive the full
      // getUserMedia → MediaRecorder → WebSocket → backend path without
      // any mock. See docs/testing-strategy.md.
      args: [
        '--use-fake-ui-for-media-stream',
        '--use-fake-device-for-media-stream',
        `--use-file-for-fake-audio-capture=${SPEAK_FIXTURE_WAV}`,
      ],
    },
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Start both frontend and backend before tests */
  webServer: [
    {
      command: 'cd ../backend && python3 -m uvicorn main:app --port 8100',
      url: 'http://localhost:8100/api/meta',
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
    {
      command: 'npm run dev -- --port 5200 --strictPort',
      url: 'http://localhost:5200',
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
  ],
});
