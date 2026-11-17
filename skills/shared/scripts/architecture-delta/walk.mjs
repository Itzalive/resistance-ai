// Checks a model folder before likec4 loads it, and checks the C4 specification copy.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from './errors.mjs';

export const MODEL_FILE_LIMIT = 2000;
export const MODEL_BYTES_LIMIT = 50 * 1024 * 1024;
const CONFIG_NAME = /likec4\.config|likec4rc/i;

const GENERATED = 'generated';
const SOURCE = /\.(c4|likec4|like-c4)$/i;

// Spec (docs): the `generated` folder at the model folder's root counts toward its own limits, and holds no LikeC4 source.
export function walkModelDir(dir) {
  const zones = { model: { files: 0, bytes: 0, label: '' }, generated: { files: 0, bytes: 0, label: `${GENERATED}: ` } };
  const pending = [dir];
  while (pending.length > 0) {
    const current = pending.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const full = path.join(current, entry.name);
      const parts = path.relative(dir, full).split(path.sep);
      const rel = parts.join('/');
      if (entry.isSymbolicLink()) throw new ToolError('model-symlink', `${rel} is a link`);
      if (CONFIG_NAME.test(entry.name)) throw new ToolError('model-config', `${rel} is a likec4 config file`);
      if (entry.isDirectory()) {
        pending.push(full);
        continue;
      }
      // The folder name is matched in any case, as case-insensitive file systems treat it.
      const zone = parts.length > 1 && parts[0].toLowerCase() === GENERATED ? zones.generated : zones.model;
      if (zone === zones.generated && SOURCE.test(entry.name)) {
        throw new ToolError('model-error', `${rel} is a LikeC4 source file in the generated folder`);
      }
      zone.files += 1;
      if (zone.files > MODEL_FILE_LIMIT) throw new ToolError('model-size', `${zone.label}more than ${MODEL_FILE_LIMIT} files`);
      zone.bytes += fs.statSync(full).size;
      if (zone.bytes > MODEL_BYTES_LIMIT) throw new ToolError('model-size', `${zone.label}more than 50 MB in total`);
    }
  }
}

export function checkSpecCopy(modelDir, shippedPath) {
  const copy = path.join(modelDir, 'c4.c4');
  if (!fs.existsSync(copy)) throw new ToolError('spec-copy', 'c4.c4 is missing from the model folder');
  const lf = (text) => text.replace(/\r\n/g, '\n');
  if (lf(fs.readFileSync(copy, 'utf8')) !== lf(fs.readFileSync(shippedPath, 'utf8'))) {
    throw new ToolError('spec-copy', 'c4.c4 differs from the shipped specification');
  }
}
