// The documents of one build, as { path with '/': text }, and the output limits (write rule 4).
import { ToolError, clean, cleanText } from '../architecture-delta/errors.mjs';
import { exportJson } from '../architecture-delta/report.mjs';
import { buildOverview } from './overview.mjs';
import { renderMarkdown } from './markdown.mjs';
import { renderHtml, pageHref } from './html.mjs';
import { drawFigures } from './svg.mjs';
import { buildPack } from './pack.mjs';
import { IMPROVEMENTS, areaDoc, capabilityDoc, changeDoc, documentBase } from './facts.mjs';
import { buildArea } from './area.mjs';
import { buildCapability } from './capability.mjs';
import { buildChange } from './change.mjs';
import { buildImprovements } from './improvements.mjs';

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

// A document's Markdown file and its HTML page, whose diagrams are drawn as SVG.
async function addDocument(files, rel, tree) {
  files[rel] = renderMarkdown(tree);
  files[pageHref(rel)] = renderHtml(await drawFigures(tree));
}

// Spec, What each document holds: every document is built from the export (and the cleaned known-gap entries).
export async function buildFiles(model, records, gap, tick = () => {}) {
  const data = exportJson(model, records);
  const files = {};
  files['pack/model.json'] = `${JSON.stringify({ generated: 'architecture-docs', export: data }, null, 2)}\n`;
  tick();
  Object.assign(files, buildPack(data, gap, tick));
  await addDocument(files, 'README.md', buildOverview(data, gap));
  tick();
  const base = documentBase(data);
  for (const area of data.areas) {
    await addDocument(files, areaDoc(area.name), buildArea(data, gap, area, base));
    tick();
  }
  for (const capability of data.capabilities) {
    await addDocument(files, capabilityDoc(capability.name), buildCapability(data, capability, base));
    tick();
  }
  for (const change of data.changes) {
    await addDocument(files, changeDoc(change.id), buildChange(data, gap, change, base));
    tick();
  }
  await addDocument(files, IMPROVEMENTS, buildImprovements(data, gap, base));
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
