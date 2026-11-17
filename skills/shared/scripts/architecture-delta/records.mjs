// Reads and validates the record files of an architecture model folder.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from './errors.mjs';
import { isObject, shapeProblems } from './records-shape.mjs';
import { cmp } from './report.mjs';

const GROUP_FILE = /^[a-z0-9]+(-[a-z0-9]+)*\.json$/;
const CHANGE_FILE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(-[a-z0-9]+)*\.json$/;
const FOLDERS = [
  { folder: 'changes', kind: 'change', pattern: CHANGE_FILE },
  { folder: 'contracts', kind: 'contracts', pattern: GROUP_FILE },
  { folder: 'decisions', kind: 'decisions', pattern: GROUP_FILE },
];

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

const RECORD_ID = /^[A-Za-z0-9][A-Za-z0-9.-]*$/;
const DATE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
const STATUS = ['current', 'partly-built', 'planned', 'superseded'];
const DECISION_EVIDENCE = ['checked', 'code', 'spec'];
const HOLE_EVIDENCE = ['checked', 'code', 'spec', 'search'];
const RUNS = ['baseline', 'epic', 'later-stage'];

const isString = (value) => typeof value === 'string';
const isRecordId = (value) => isString(value) && RECORD_ID.test(value);
const oneOf = (values) => `must be one of ${values.join(', ')}`;
const list = (value) => (Array.isArray(value) ? value : []);
const has = (record, key) => Object.hasOwn(record, key);

function isRealDate(value) {
  if (!DATE.test(value)) return false;
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

// The record lists of a decisions or contracts file, as [list name, records] with object records only.
function recordLists(file) {
  const names = file.kind === 'decisions' ? ['decisions', 'holes'] : file.kind === 'contracts' ? ['contracts'] : [];
  return names.map((name) => [name, list(file.data[name]).map((record, index) => ({ record, index }))
    .filter(({ record }) => isObject(record))]);
}

// Each object record of a file, with its path and list name, in file position order.
function eachRecord(file, visit) {
  for (const [name, records] of recordLists(file)) {
    for (const { record, index } of records) visit(record, `${name}[${index}]`, name);
  }
}

// Pass 3 for one file: record id forms and duplicates, change ids, empty element ids, reference forms.
function idPass(file, add, firstSeen) {
  const emptyElement = (value, at) => {
    if (value === '') add(at, 'must not be empty');
  };
  const referenceForm = (value, at) => {
    if (isString(value) && !RECORD_ID.test(value)) add(at, 'not a valid record id');
  };
  eachRecord(file, (record, at, name) => {
    if (!isString(record.id)) return;
    if (!RECORD_ID.test(record.id)) {
      add(`${at}.id`, 'not a valid record id');
      return;
    }
    if (firstSeen.has(record.id)) add(`${at}.id`, `duplicate id ${record.id}, first in ${firstSeen.get(record.id)}`);
    else firstSeen.set(record.id, file.at);
    if (name === 'contracts') emptyElement(record.owner, `${at}.owner`);
    const elementList = name === 'contracts' ? 'bound' : 'binds';
    list(record[elementList]).forEach((item, index) => emptyElement(item, `${at}.${elementList}[${index}]`));
    if (name === 'decisions') referenceForm(record.superseded_by, `${at}.superseded_by`);
    if (name === 'decisions') emptyElement(record.owner, `${at}.owner`);
    if (name === 'contracts') list(record.decisions).forEach((item, index) => referenceForm(item, `${at}.decisions[${index}]`));
  });
  const { data } = file;
  if (file.kind === 'change') {
    if (isString(data.id) && data.id !== file.name) add('id', `must equal the file name ${file.name}`);
    for (const key of ['elements', 'decisions', 'holes', 'contracts']) {
      if (!isObject(data[key])) continue;
      for (const part of ['added', 'changed', 'removed']) {
        list(data[key][part]).forEach((item, index) => {
          const at = `${key}.${part}[${index}]`;
          if (key === 'elements') emptyElement(item, at);
          else referenceForm(item, at);
        });
      }
    }
  }
  if (file.kind === 'coverage') {
    list(data.edge_nodes).forEach((node, index) => {
      if (isObject(node)) emptyElement(node.element, `edge_nodes[${index}].element`);
    });
  }
}

// Pass 4 for one file: element ids, decision references and coverage runs that name something real.
function linkPass(file, add, elements, decisions, changes) {
  const element = (value, at) => {
    if (isString(value) && value !== '' && !elements.has(value)) add(at, `${value} is not a model element`);
  };
  const elementList = (values, at) => {
    const seen = new Set();
    list(values).forEach((value, index) => {
      element(value, `${at}[${index}]`);
      if (!isString(value) || value === '') return;
      if (seen.has(value)) add(`${at}[${index}]`, `${value} is listed twice`);
      seen.add(value);
    });
  };
  const run = (value, at) => {
    if (isString(value) && !changes.has(value)) add(at, `${value} names no change file`);
  };
  eachRecord(file, (record, at, name) => {
    if (!isRecordId(record.id)) return;
    if (name === 'contracts') {
      element(record.owner, `${at}.owner`);
      elementList(record.bound, `${at}.bound`);
      const seen = new Set();
      list(record.decisions).forEach((value, index) => {
        if (!isRecordId(value)) return;
        if (!decisions.has(value)) add(`${at}.decisions[${index}]`, `${value} names no decision`);
        if (seen.has(value)) add(`${at}.decisions[${index}]`, `${value} is listed twice`);
        seen.add(value);
      });
      return;
    }
    elementList(record.binds, `${at}.binds`);
    if (name === 'decisions' && isRecordId(record.superseded_by)) {
      if (record.superseded_by === record.id) add(`${at}.superseded_by`, 'names its own id');
      else if (!decisions.has(record.superseded_by)) add(`${at}.superseded_by`, `${record.superseded_by} names no decision`);
    }
    if (name === 'decisions') element(record.owner, `${at}.owner`);
  });
  if (file.kind === 'coverage') {
    list(file.data.baselined).forEach((entry, index) => {
      if (isObject(entry)) run(entry.run, `baselined[${index}].run`);
    });
    list(file.data.edge_nodes).forEach((node, index) => {
      if (!isObject(node)) return;
      element(node.element, `edge_nodes[${index}].element`);
      run(node.run, `edge_nodes[${index}].run`);
    });
  }
}

// Pass 5 for one file: list order, the supersession rule, fixed values and dates.
function valuePass(file, add) {
  const fixed = (record, key, values, at) => {
    if (isString(record[key]) && !values.includes(record[key])) add(at, oneOf(values));
  };
  for (const [name, records] of recordLists(file)) {
    const kept = records.filter(({ record }) => isRecordId(record.id));
    const k = kept.findIndex(({ record }, j) => j > 0 && cmp(record.id, kept[j - 1].record.id) < 0);
    const late = k === -1 ? null : { index: kept[k].index, after: kept[k - 1].record.id };
    for (const { record, index } of records) {
      const at = `${name}[${index}]`;
      if (late !== null && index === late.index) add(`${at}.id`, `not sorted by id: ${record.id} comes after ${late.after}`);
      if (name === 'decisions') {
        fixed(record, 'status', STATUS, `${at}.status`);
        if (isString(record.status) && (!has(record, 'superseded_by') || isString(record.superseded_by))) {
          if (record.status === 'superseded' && !has(record, 'superseded_by')) add(`${at}.superseded_by`, 'required when status is superseded');
          if (record.status !== 'superseded' && has(record, 'superseded_by')) add(`${at}.superseded_by`, 'only allowed when status is superseded');
        }
        fixed(record, 'evidence', DECISION_EVIDENCE, `${at}.evidence`);
        if (isString(record.owner) && !has(record, 'obligations')) add(`${at}.obligations`, 'required when owner is set');
      }
      if (name === 'holes') fixed(record, 'evidence', HOLE_EVIDENCE, `${at}.evidence`);
    }
  }
  if (file.kind === 'change') {
    const { data } = file;
    if (isString(data.date)) {
      if (!isRealDate(data.date)) add('date', 'not a real date');
      if (data.date !== file.name.slice(0, 10)) add('date', 'must be the start of the file name');
    }
    fixed(data, 'run', RUNS, 'run');
    if (isObject(data.check) && Number.isInteger(data.check.exit) && data.check.exit !== 0 && data.check.exit !== 1) {
      add('check.exit', 'must be 0 or 1');
    }
    if (isObject(data.approved) && isString(data.approved.date) && !isRealDate(data.approved.date)) {
      add('approved.date', 'not a real date');
    }
  }
}

// Passes 3 to 5, file by file in folder order; a duplicate id is reported where it occurs second.
function laterPasses(files, elements, changes) {
  const out = [];
  const decisions = new Set();
  for (const file of files) {
    if (file.kind !== 'decisions') continue;
    for (const record of list(file.data.decisions)) if (isObject(record) && isRecordId(record.id)) decisions.add(record.id);
  }
  const firstSeen = new Map();
  for (const file of files) {
    const add = (field, message) => out.push(problem(file.at, field, message));
    idPass(file, add, firstSeen);
    linkPass(file, add, elements, decisions, changes);
    valuePass(file, add);
  }
  return out;
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
      for (const listName of lists) for (const record of data[listName]) out[listName].push({ ...record, group: name });
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
