import { existsSync, unlinkSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const FLAG_PATH = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
  '..',
  'backend',
  '.mock_jev_flag',
);

export default async function globalTeardown() {
  if (existsSync(FLAG_PATH)) {
    unlinkSync(FLAG_PATH);
  }
}
