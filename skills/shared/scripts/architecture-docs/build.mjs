// The documents of one build, as { path with '/': text }, and the output limits (write rule 4).
import { ToolError } from '../architecture-delta/errors.mjs';
import { exportJson } from '../architecture-delta/report.mjs';

export const OUT_FILE_LIMIT = 2000;
export const OUT_BYTES_LIMIT = 50 * 1024 * 1024;

// Spec, AI pack: `pack/model.json` holds the format 4 export under `export`, marked by its first key.
// Later plans add the other documents here; `gap` (cleaned known-gap entries) is for them.
export function buildFiles(model, records, gap, tick = () => {}) {
  const files = {};
  files['pack/model.json'] = `${JSON.stringify({ generated: 'architecture-docs', export: exportJson(model, records) }, null, 2)}\n`;
  tick();
  return files;
}

// Spec, write rule 4: a build over 2,000 files or 50 MB stops before writing.
export function checkLimits(files) {
  const names = Object.keys(files);
  if (names.length > OUT_FILE_LIMIT) throw new ToolError('out-error', `the output would be more than ${OUT_FILE_LIMIT} files`);
  const bytes = names.reduce((sum, rel) => sum + Buffer.byteLength(files[rel], 'utf8'), 0);
  if (bytes > OUT_BYTES_LIMIT) throw new ToolError('out-error', 'the output would be more than 50 MB');
}
