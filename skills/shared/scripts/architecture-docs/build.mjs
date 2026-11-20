// The documents of one build, as { path with '/': text }, and the output limits (write rule 4).
import { ToolError, clean, cleanText } from '../architecture-delta/errors.mjs';
import { exportJson } from '../architecture-delta/report.mjs';
import { buildOverview } from './overview.mjs';
import { renderMarkdown } from './markdown.mjs';
import { renderHtml } from './html.mjs';

export const OUT_FILE_LIMIT = 2000;
export const OUT_BYTES_LIMIT = 50 * 1024 * 1024;

// Spec, The tool: known-gap entries are cleaned like `export` output before any document uses them.
export function cleanGap(entries) {
  return entries.map((entry) => ({
    from: clean(entry.from),
    to: clean(entry.to),
    reason: cleanText(entry.reason),
    close_by: entry.close_by === null ? null : cleanText(entry.close_by),
  }));
}

// Spec, What each document holds: every document is built from the export (and the cleaned known-gap entries).
export function buildFiles(model, records, gap, tick = () => {}) {
  const data = exportJson(model, records);
  const files = {};
  files['pack/model.json'] = `${JSON.stringify({ generated: 'architecture-docs', export: data }, null, 2)}\n`;
  tick();
  const overview = buildOverview(data, gap);
  files['README.md'] = renderMarkdown(overview);
  files['index.html'] = renderHtml(overview);
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
