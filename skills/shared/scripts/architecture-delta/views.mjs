// Area and capability views: read from LikeC4's computed model and checked against the model's elements.
import { ToolError } from './errors.mjs';
import { cmp } from './report.mjs';

export const AREA = 'area-';
export const CAPABILITY = 'capability-';
const NAME = /^[a-z0-9][a-z0-9-]{0,63}$/;
const RESERVED = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/;

// Spec, Terms: X is inside Y when X's id starts with Y's id and a dot; here an id also counts as inside itself.
export const within = (id, outer) => id === outer || id.startsWith(`${outer}.`);

function shapeError(detail) {
  return new ToolError('internal', `likec4 returned ${detail}`);
}

export function richText(value) {
  return value && value.isEmpty === false && typeof value.md === 'string' ? value.md : null;
}

function readView(view) {
  if (typeof view?.id !== 'string' || view.$view === null || typeof view.$view !== 'object') {
    throw shapeError('a view without a string id');
  }
  const data = view.$view;
  if (typeof data._type !== 'string' || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
    throw shapeError(`view ${view.id} without a type, nodes and edges`);
  }
  const title = data.title ?? null;
  if (title !== null && typeof title !== 'string') throw shapeError(`view ${view.id} with a non-string title`);
  return {
    id: view.id,
    type: data._type,
    title: title ?? view.id,
    description: richText(view.description),
    viewOf: typeof data.viewOf === 'string' ? data.viewOf : null,
    nodes: data.nodes,
    edges: data.edges,
  };
}

// Spec, Areas: a scoped view's elements are its scope and everything inside it; an unscoped view's are the element nodes it draws.
function areaElements(view, elementIds) {
  if (view.viewOf !== null) return elementIds.filter((id) => within(id, view.viewOf));
  const known = new Set(elementIds);
  return [...new Set(view.nodes.map((node) => node?.modelRef).filter((ref) => typeof ref === 'string' && known.has(ref)))];
}

function typeProblem(view, prefix) {
  const wanted = prefix === AREA ? 'element' : 'dynamic';
  if (view.type === wanted) return null;
  return prefix === AREA ? 'an area view must be an element view' : 'a capability view must be a dynamic view';
}

// Spec, Capabilities: a relationship matches a step from A to B when its source is A or inside A and its target is B or inside B.
function readSteps(view, relationships, add) {
  const refs = new Map(view.nodes.map((node) => [node?.id, node?.modelRef]));
  return view.edges.map((edge, index) => {
    const from = refs.get(edge?.source);
    const to = refs.get(edge?.target);
    if (typeof from !== 'string' || typeof to !== 'string') throw shapeError(`view ${view.id} with a step between non-elements`);
    const forward = relationships.filter((r) => within(r.from, from) && within(r.to, to));
    const back = forward.length > 0 ? [] : relationships.filter((r) => within(r.from, to) && within(r.to, from));
    if (forward.length === 0 && back.length === 0) add(`step ${index + 1}: ${from} -> ${to} follows no relationship`, index + 1);
    const kinds = [...new Set((forward.length > 0 ? forward : back).map((r) => r.kind ?? 'uses'))].sort(cmp);
    const label = typeof edge.label === 'string' && edge.label !== '' ? edge.label : null;
    return { from, to, label, reply: forward.length === 0, kinds };
  });
}

// The area and capability views, or one `model-error` naming every problem, sorted by view id, then step.
export function readViews(computed, elementIds, relationships, runtime) {
  if (typeof computed.views !== 'function') throw shapeError('a model without views()');
  const all = [...relationships.map((r) => ({ ...r, kind: null })), ...runtime];
  const problems = [];
  const areas = [];
  const capabilities = [];
  for (const raw of computed.views()) {
    const view = readView(raw);
    const prefix = view.id.startsWith(AREA) ? AREA : view.id.startsWith(CAPABILITY) ? CAPABILITY : null;
    if (prefix === null) continue;
    const add = (message, step = 0) => problems.push({ view: view.id, step, line: `view ${view.id}: ${message}` });
    const wrongType = typeProblem(view, prefix);
    if (wrongType !== null) {
      add(wrongType);
      continue;
    }
    const name = view.id.slice(prefix.length);
    if (!NAME.test(name) || RESERVED.test(name)) {
      add(`${name} is not a valid name`);
      continue;
    }
    const entry = { name, title: view.title, description: view.description };
    if (prefix === AREA) areas.push({ ...entry, elements: areaElements(view, elementIds).sort(cmp) });
    else capabilities.push({ ...entry, steps: readSteps(view, all, add) });
  }
  if (problems.length > 0) {
    problems.sort((x, y) => cmp(x.view, y.view) || x.step - y.step);
    throw new ToolError('model-error', problems.map((item) => item.line));
  }
  return { areas: areas.sort((x, y) => cmp(x.name, y.name)), capabilities: capabilities.sort((x, y) => cmp(x.name, y.name)) };
}
