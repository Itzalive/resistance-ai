// Reads and validates the dependency, known-gap and shards files.
import fs from 'node:fs';
import { ToolError } from './errors.mjs';

export const FILE_LIMIT = 50 * 1024 * 1024;
export const EDGE_LIMIT = 1_000_000;

function bad(detail) {
  return new ToolError('bad-input', detail);
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function onlyKeys(value, allowed, where) {
  for (const key of Object.keys(value)) if (!allowed.includes(key)) throw bad(`${where}: unknown key ${key}`);
}

function text(value) {
  return typeof value === 'string' && value !== '';
}

export function readJson(file, flag) {
  if (fs.statSync(file).size > FILE_LIMIT) throw new ToolError('file-size', `${flag} is over 50 MB`);
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (err) {
    throw bad(`${flag} is not valid JSON: ${err.message}`);
  }
}

export function parseDeps(data) {
  if (!isObject(data) || !Object.hasOwn(data, 'edges')) throw bad('--deps must be an object with an edges list');
  onlyKeys(data, ['edges'], '--deps');
  if (!Array.isArray(data.edges)) throw bad('--deps edges must be a list');
  if (data.edges.length > EDGE_LIMIT) throw new ToolError('edge-cap', `more than ${EDGE_LIMIT} edges`);
  const seen = new Set();
  const edges = [];
  data.edges.forEach((edge, index) => {
    if (!Array.isArray(edge) || edge.length !== 2 || !edge.every(text)) {
      throw bad(`--deps edge ${index} must be two non-empty strings`);
    }
    const key = `${edge[0]}\u0000${edge[1]}`;
    if (!seen.has(key)) {
      seen.add(key);
      edges.push([edge[0], edge[1]]);
    }
  });
  return edges;
}

export function parseGap(data, elementIds) {
  const ids = new Set(elementIds);
  if (!isObject(data) || !Array.isArray(data.entries)) throw bad('--gap must be an object with an entries list');
  onlyKeys(data, ['entries'], '--gap');
  const seen = new Set();
  return data.entries.map((entry, index) => {
    const where = `--gap entry ${index}`;
    if (!isObject(entry)) throw bad(`${where} must be an object`);
    onlyKeys(entry, ['from', 'to', 'reason', 'close_by'], where);
    for (const key of ['from', 'to', 'reason']) if (!text(entry[key])) throw bad(`${where}: ${key} must be a non-empty string`);
    if (entry.close_by !== undefined && typeof entry.close_by !== 'string') throw bad(`${where}: close_by must be a string`);
    for (const key of ['from', 'to']) if (!ids.has(entry[key])) throw bad(`${where}: ${entry[key]} is not a model element`);
    const pair = `${entry.from}\u0000${entry.to}`;
    if (seen.has(pair)) throw bad(`${where} duplicates ${entry.from} -> ${entry.to}`);
    seen.add(pair);
    return { from: entry.from, to: entry.to, reason: entry.reason, close_by: entry.close_by ?? null };
  });
}

export function parseShards(data, elementIds) {
  const ids = new Set(elementIds);
  if (!isObject(data) || !isObject(data.shards)) throw bad('--shards must be an object with a shards object');
  onlyKeys(data, ['shards'], '--shards');
  const shards = {};
  for (const [name, list] of Object.entries(data.shards)) {
    if (!Array.isArray(list)) throw bad(`--shards ${name} must be a list of element ids`);
    for (const id of list) if (typeof id !== 'string' || !ids.has(id)) throw bad(`--shards ${name}: ${id} is not a model element`);
    shards[name] = [...list];
  }
  return shards;
}
