// Loads a model folder with likec4, checks the shape of what likec4 returns, validates code prefixes.
import path from 'node:path';
import { ToolError } from './errors.mjs';

export const ELEMENT_LIMIT = 5000;

function shapeError(detail) {
  return new ToolError('internal', `likec4 returned ${detail}`);
}

function where(err, modelDir) {
  const file = typeof err?.sourceFsPath === 'string' ? path.relative(modelDir, err.sourceFsPath) : '?';
  const line = typeof err?.line === 'number' ? err.line + 1 : '?';
  return `${file}:${line}: ${err?.message ?? 'unknown error'}`;
}

function splitList(value) {
  return value === undefined ? [] : value.split(',').map((item) => item.trim());
}

function validatePrefixes(elements) {
  const seen = new Map();
  for (const element of elements) {
    for (const prefix of element.code) {
      if (prefix === '') throw new ToolError('model-error', `${element.id}: empty code prefix`);
      if (seen.has(prefix)) {
        throw new ToolError('model-error', `${element.id}: duplicate code prefix ${prefix}, also listed by ${seen.get(prefix)}`);
      }
      seen.set(prefix, element.id);
    }
  }
}

export async function loadModel(LikeC4, modelDir) {
  let workspace;
  let computed;
  try {
    workspace = await LikeC4.fromWorkspace(modelDir, { logger: false });
  } catch (err) {
    throw new ToolError('model-error', err?.message ?? String(err));
  }
  const errors = workspace.getErrors();
  if (!Array.isArray(errors)) throw shapeError('getErrors() that is not a list');
  if (errors.length > 0) throw new ToolError('model-error', errors.map((err) => where(err, modelDir)));
  try {
    computed = await workspace.computedModel();
  } catch (err) {
    throw new ToolError('model-error', err?.message ?? String(err));
  }
  const elements = [];
  for (const element of computed.elements()) {
    if (typeof element?.id !== 'string' || typeof element.kind !== 'string') throw shapeError('an element without a string id and kind');
    if (!Array.isArray(element.tags) || !element.tags.every((tag) => typeof tag === 'string')) throw shapeError(`element ${element.id} without a tags list`);
    if (typeof element.getMetadata !== 'function') throw shapeError(`element ${element.id} without getMetadata`);
    const meta = element.getMetadata() ?? {};
    for (const key of ['code', 'rules']) {
      if (meta[key] !== undefined && typeof meta[key] !== 'string') throw shapeError(`element ${element.id} with a non-string ${key}`);
    }
    elements.push({
      id: element.id,
      kind: element.kind,
      tags: [...element.tags],
      code: splitList(meta.code),
      rules: splitList(meta.rules).filter((rule) => rule !== ''),
    });
    if (elements.length > ELEMENT_LIMIT) throw new ToolError('element-cap', `more than ${ELEMENT_LIMIT} elements`);
  }
  const relationships = [];
  for (const relationship of computed.relationships()) {
    if (typeof relationship?.source?.id !== 'string' || typeof relationship?.target?.id !== 'string') {
      throw shapeError('a relationship without string source and target ids');
    }
    relationships.push({ from: relationship.source.id, to: relationship.target.id });
  }
  validatePrefixes(elements);
  return { elements, relationships };
}
