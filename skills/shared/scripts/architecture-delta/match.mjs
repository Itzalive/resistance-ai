// Compares a validated model with code dependencies, following the spec's matching rules.

const key = (a, b) => `${a}\u0000${b}`;

export function within(id, root) {
  return id === root || id.startsWith(`${root}.`);
}

function ancestorsOrSelf(id) {
  const parts = id.split('.');
  return parts.map((_, i) => parts.slice(0, i + 1).join('.'));
}

export function compare(model, edges, options) {
  const { separator, gap = [], scope = null, shards = null, tick = () => {} } = options;
  const elements = new Map(model.elements.map((element) => [element.id, element]));
  const prefixes = model.elements
    .flatMap((element) => element.code.map((prefix) => [prefix, element.id]))
    .sort((a, b) => b[0].length - a[0].length);
  const mapped = new Map();
  const mapModule = (module) => {
    if (!mapped.has(module)) {
      const hit = prefixes.find(([prefix]) => module === prefix || module.startsWith(prefix + separator));
      mapped.set(module, hit ? hit[1] : null);
    }
    return mapped.get(module);
  };
  const relationships = [];
  const relationshipKeys = new Set();
  for (const r of model.relationships) {
    if (!relationshipKeys.has(key(r.from, r.to))) {
      relationshipKeys.add(key(r.from, r.to));
      relationships.push({ from: r.from, to: r.to });
    }
  }
  const nearestProtected = (id) =>
    ancestorsOrSelf(id).reverse().find((x) => elements.get(x)?.tags.includes('protected')) ?? null;
  const allowed = (a, b) => {
    const sources = ancestorsOrSelf(a);
    const guard = nearestProtected(b);
    if (guard !== null && !within(a, guard)) {
      return relationships.some((r) => sources.includes(r.from) && within(r.to, guard));
    }
    const targets = ancestorsOrSelf(b);
    return relationships.some((r) => sources.includes(r.from) && targets.includes(r.to));
  };

  const unmapped = new Set();
  const breachByPair = new Map();
  const allowedByPair = new Map();
  const checkedPairs = [];
  edges.forEach(([from, to], index) => {
    if (index > 0 && index % 10000 === 0) tick();
    const source = mapModule(from);
    if (source === null) {
      unmapped.add(from);
      return;
    }
    const target = mapModule(to);
    if (target === null || within(source, target) || within(target, source)) return;
    const pair = key(source, target);
    if (!allowedByPair.has(pair)) {
      allowedByPair.set(pair, allowed(source, target));
      checkedPairs.push([source, target]);
    }
    if (allowedByPair.get(pair)) return;
    if (!breachByPair.has(pair)) breachByPair.set(pair, { from: source, to: target, edges: [] });
    breachByPair.get(pair).edges.push([from, to]);
  });

  const hasCode = (id) => (elements.get(id)?.code.length ?? 0) > 0;
  const notYetReached = relationships.filter(
    (r) => hasCode(r.from) && hasCode(r.to) && !checkedPairs.some(([s, t]) => within(s, r.from) && within(t, r.to)),
  );
  const entryKeys = new Set(gap.map((entry) => key(entry.from, entry.to)));
  const allBreaches = [...breachByPair.values()].map((breach) => ({
    ...breach,
    gap: entryKeys.has(key(breach.from, breach.to)) ? 'known' : 'new',
  }));
  const staleEverywhere = gap
    .filter((entry) => !breachByPair.has(key(entry.from, entry.to)))
    .map(({ from, to }) => ({ from, to }));
  const inScope = (id) => scope === null || scope.some((root) => within(id, root));
  const keep = (pair) => inScope(pair.from) || inScope(pair.to);
  const breaches = allBreaches.filter(keep);
  const known = breaches.filter((b) => b.gap === 'known').map(({ from, to }) => ({ from, to }));
  const fresh = breaches.filter((b) => b.gap === 'new').map(({ from, to }) => ({ from, to }));
  const stale = staleEverywhere.filter(keep);
  const hotSpots = [];
  if (shards !== null) {
    for (const id of elements.keys()) {
      const names = Object.keys(shards).filter((name) => shards[name].some((root) => within(id, root)));
      if (names.length >= 2) hotSpots.push({ element: id, shards: names });
    }
  }
  return {
    breaches,
    notYetReached: notYetReached.filter(keep),
    unmapped: [...unmapped],
    hotSpots,
    gap: { known, new: fresh, stale },
    exitCode: fresh.length > 0 || stale.length > 0 ? 1 : 0,
  };
}
