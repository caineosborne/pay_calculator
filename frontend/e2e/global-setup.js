import { rm, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';

// Custom awards are filesystem-backed. Reset only the dedicated E2E directory
// before each run so configuration names and results stay deterministic.
export default async function globalSetup() {
  const directory = resolve(process.cwd(), '../test-results/e2e-custom-rules');
  await rm(directory, { recursive: true, force: true });
  await mkdir(directory, { recursive: true });
}
