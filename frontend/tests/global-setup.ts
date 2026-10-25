import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// backend/practice_scoring.py polls this sentinel file (in addition to the
// MOCK_JEV env var) because langHero's backend is a long-lived systemd
// process — a shell-scoped env var never reaches it. See practice_scoring.py.
const FLAG_PATH = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
  '..',
  'backend',
  '.mock_jev_flag',
);

export default async function globalSetup() {
  if (process.env.MOCK_JEV === '1') {
    writeFileSync(FLAG_PATH, '');
  }
}
