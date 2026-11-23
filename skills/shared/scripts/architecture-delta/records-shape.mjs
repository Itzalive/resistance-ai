// The record tables of the architecture model folder, and the shape pass (pass 2b) over one parsed file.

// A field spec: name, type, required; `of` for list items, `fields` for objects, `minOne` for lists that need an item,
// `id` ('record' or 'element') for values that hold ids. `string` is any string: ids, and values checked in pass 5.
const field = (name, type, extra = {}) => ({ name, type, required: true, ...extra });
const optional = (name, type, extra = {}) => ({ name, type, required: false, ...extra });
const TEXT = { type: 'text' };
const ids = (id) => ({ type: 'string', id });
const object = (fields) => ({ type: 'object', fields });
const changeLists = (id) => [field('added', 'list', { of: ids(id) }), field('changed', 'list', { of: ids(id) }),
  field('removed', 'list', { of: ids(id) })];
// A change file's relationship (#43): its ends, its kind (null for an import relationship) and its titles.
const RELATIONSHIP = object([field('from', 'string', { id: 'element' }), field('to', 'string', { id: 'element' }),
  field('kind', 'textOrNull'), field('titles', 'list', { of: TEXT })]);
const relationshipLists = [field('added', 'list', { of: RELATIONSHIP }), field('changed', 'list', { of: RELATIONSHIP }),
  field('removed', 'list', { of: RELATIONSHIP })];

export const DECISION = [
  field('id', 'string', { id: 'record' }),
  field('decision', 'text'),
  field('reason', 'textOrNull'),
  field('rejected', 'list', { of: TEXT }),
  field('binds', 'list', { of: ids('element') }),
  field('status', 'string'),
  optional('superseded_by', 'string', { id: 'record' }),
  field('evidence', 'string'),
  field('sources', 'list', { of: TEXT }),
  optional('owner', 'string', { id: 'element' }),
  optional('obligations', 'list', { of: TEXT, minOne: true }),
  optional('compatibility', 'text'),
  optional('capabilities', 'list', { of: TEXT }),
  optional('note', 'text'),
];

export const HOLE = [
  field('id', 'string', { id: 'record' }),
  field('what', 'text'),
  field('binds', 'list', { of: ids('element') }),
  field('evidence', 'string'),
  optional('note', 'text'),
];

export const CONTRACT = [
  field('id', 'string', { id: 'record' }),
  field('name', 'text'),
  field('owner', 'string', { id: 'element' }),
  field('bound', 'list', { of: ids('element'), minOne: true }),
  field('obligations', 'list', { of: TEXT, minOne: true }),
  field('compatibility', 'textOrNull'),
  optional('notes', 'list', { of: TEXT }),
  optional('decisions', 'list', { of: ids('record') }),
  optional('capabilities', 'list', { of: TEXT }),
];

export const TABLES = {
  decisions: [
    field('title', 'text'),
    field('decisions', 'list', { of: object(DECISION) }),
    field('holes', 'list', { of: object(HOLE) }),
  ],
  contracts: [field('title', 'text'), field('contracts', 'list', { of: object(CONTRACT) })],
  change: [
    field('id', 'string'),
    field('date', 'string'),
    field('run', 'string'),
    field('asked_by', 'text'),
    field('summary', 'text'),
    field('rejected', 'list', { of: TEXT }),
    field('elements', 'object', { fields: changeLists('element') }),
    field('decisions', 'object', { fields: changeLists('record') }),
    field('holes', 'object', { fields: changeLists('record') }),
    field('contracts', 'object', { fields: changeLists('record') }),
    // Absent in a change file written before #43.
    optional('relationships', 'object', { fields: relationshipLists }),
    field('gap', 'object', { fields: [field('added', 'list', { of: { type: 'pair' } }), field('removed', 'list', { of: { type: 'pair' } })] }),
    field('check', 'object', { fields: [field('exit', 'exit'), field('summary', 'text'), field('output', 'text')] }),
    field('approved', 'objectOrNull', { fields: [field('by', 'text'), field('date', 'string')] }),
  ],
  coverage: [
    field('answer', 'text'),
    field('baselined', 'list', { of: object([field('prefix', 'text'), field('run', 'string')]) }),
    field('edge_nodes', 'list', { of: object([field('element', 'string', { id: 'element' }), field('run', 'string')]) }),
    field('counts', 'object', { fields: [field('modules', 'count'), field('groups', 'count')] }),
    field('unmapped', 'list', { of: object([field('module', 'text'), field('reason', 'text')]) }),
  ],
};

export const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const isText = (value) => typeof value === 'string' && value !== '';

const TYPES = {
  text: [isText, 'must be a non-empty string'],
  textOrNull: [(value) => value === null || isText(value), 'must be a non-empty string or null'],
  string: [(value) => typeof value === 'string', 'must be a string'],
  list: [Array.isArray, 'must be a list'],
  object: [isObject, 'must be an object'],
  objectOrNull: [(value) => value === null || isObject(value), 'must be an object or null'],
  count: [(value) => Number.isInteger(value) && value >= 0, 'must be a whole number of 0 or more'],
  exit: [Number.isInteger, 'must be a whole number'],
  pair: [(value) => Array.isArray(value) && value.length === 2 && value.every(isText), 'must be a pair of two non-empty strings'],
};

export function hasType(type, value) {
  return TYPES[type][0](value);
}

export function fieldPath(parent, key) {
  return parent === '' ? key : `${parent}.${key}`;
}

function checkValue(spec, value, at, out) {
  if (!hasType(spec.type, value)) {
    out.push({ field: at, message: TYPES[spec.type][1] });
    return;
  }
  if (spec.type === 'list') {
    if (spec.minOne && value.length === 0) out.push({ field: at, message: 'needs at least one item' });
    value.forEach((item, index) => checkValue(spec.of, item, `${at}[${index}]`, out));
  } else if (spec.fields && value !== null) {
    checkFields(spec.fields, value, at, out);
  }
}

function checkFields(fields, value, at, out) {
  for (const spec of fields) {
    const here = fieldPath(at, spec.name);
    if (!Object.hasOwn(value, spec.name)) {
      if (spec.required) out.push({ field: here, message: 'required' });
      continue;
    }
    checkValue(spec, value[spec.name], here, out);
  }
  const known = new Set(fields.map((spec) => spec.name));
  for (const key of Object.keys(value)) {
    if (!known.has(key)) out.push({ field: fieldPath(at, key), message: 'unknown field' });
  }
}

// Pass 2b: every shape problem in one parsed file, by field in table order, unknown keys last in file order.
export function shapeProblems(kind, data) {
  const out = [];
  checkFields(TABLES[kind], data, '', out);
  return out;
}
