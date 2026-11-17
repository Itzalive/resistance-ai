// Reads and validates the record files of an architecture model folder.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from './errors.mjs';
import { isObject, shapeProblems } from './records-shape.mjs';

const GROUP_FILE = /^[a-z0-9]+(-[a-z0-9]+)*\.json$/;
const CHANGE_FILE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(-[a-z0-9]+)*\.json$/;
const FOLDERS = [
  { folder: 'changes', kind: 'change', pattern: CHANGE_FILE },
  { folder: 'contracts', kind: 'contracts', pattern: GROUP_FILE },
  { folder: 'decisions', kind: 'decisions', pattern: GROUP_FILE },
];

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
const problem = (at, field, message) => ({ at, line: `${at}: ${field}: ${message}` });

// Pass 1 for one record folder: the well-named files in it, and a problem for anything else.
function listFolder(modelDir, { folder, kind, pattern }, problems, files) {
  const dir = path.join(modelDir, folder);
  if (!fs.existsSync(dir)) return;
  if (!fs.statSync(dir).isDirectory()) {
    problems.push(problem(folder, '-', 'must be a folder'));
    return;
  }
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const at = `${folder}/${entry.name}`;
    if (entry.isDirectory()) problems.push(problem(at, '-', 'folders are not allowed here'));
    else if (!pattern.test(entry.name)) problems.push(problem(at, '-', 'not a valid file name here'));
    else files.push({ at, kind, name: entry.name.slice(0, -'.json'.length), full: path.join(dir, entry.name) });
  }
}

// Pass 2a: the file as one JSON object, or a problem.
function parseFile(file, problems) {
  let data;
  try {
    data = JSON.parse(fs.readFileSync(file.full, 'utf8'));
  } catch {
    problems.push(problem(file.at, '-', 'not valid JSON'));
    return null;
  }
  if (!isObject(data)) {
    problems.push(problem(file.at, '-', 'must be a JSON object'));
    return null;
  }
  return data;
}

// Passes 3 to 5 over every file that passed 2a. Filled in by the id, link, order and value checks.
function laterPasses() {
  return [];
}

function result(files) {
  const out = { groups: [], decisions: [], holes: [], contracts: [], changes: [], coverage: null };
  for (const file of files) {
    const { data, kind, name } = file;
    if (kind === 'coverage') out.coverage = data;
    else if (kind === 'change') out.changes.push(data);
    else {
      out.groups.push({ kind, group: name, title: data.title });
      const lists = kind === 'decisions' ? ['decisions', 'holes'] : ['contracts'];
      for (const list of lists) for (const record of data[list]) out[list].push({ ...record, group: name });
    }
  }
  return out;
}

// Every record in the folder, or one `record-error` naming every problem, sorted by path then pass and position.
export function readRecords(modelDir, elementIds, tick = () => {}) {
  const problems = [];
  const files = [];
  for (const spec of FOLDERS) listFolder(modelDir, spec, problems, files);
  const coverage = path.join(modelDir, 'coverage.json');
  if (fs.existsSync(coverage)) {
    if (fs.statSync(coverage).isDirectory()) problems.push(problem('coverage.json', '-', 'must be a file'));
    else files.push({ at: 'coverage.json', kind: 'coverage', name: 'coverage', full: coverage });
  }
  files.sort((x, y) => cmp(x.at, y.at));
  const read = [];
  for (const file of files) {
    const data = parseFile(file, problems);
    tick();
    if (data === null) continue;
    for (const found of shapeProblems(file.kind, data)) problems.push(problem(file.at, found.field, found.message));
    read.push({ ...file, data });
  }
  problems.push(...laterPasses(read, new Set(elementIds), new Set(files.filter((f) => f.kind === 'change').map((f) => f.name))));
  if (problems.length > 0) {
    const sorted = problems.map((item, index) => ({ ...item, index })).sort((x, y) => cmp(x.at, y.at) || x.index - y.index);
    throw new ToolError('record-error', sorted.map((item) => item.line));
  }
  return result(read);
}
