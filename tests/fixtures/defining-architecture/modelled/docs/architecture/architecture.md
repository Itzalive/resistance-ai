# Shop architecture

## Decision log

### 2026-11-02 — baseline

- Asked by: specifying-epics (step 2b, empty folder).
- Diff: one component per group for the eight groups, a relationship per current element pair, and the `inventory -> orders` edge of the `orders`–`inventory` cycle gapped with `cycle in current code`.
- Check output:

  ```
  Known breaches
    shop.inventory -> shop.orders (1 edges)

  0 new, 0 stale, 1 known (likec4 1.60.0 from plugin)
  ```

- Reviews: self-review and independent audit passed. Owner: [ARCH-APPROVED].

### 2026-11-02 — epic run (order events)

- Asked by: specifying-epics.
- Diff: the `shop` system around the eight components; `events` (not yet built), `orders -> events` and `reporting -> events` added; `reporting -> payments` removed and gapped (BR-3); rules BR-1 to BR-5 assigned.
- Rejected alternative: each capability defines its own event shape.
- Check output:

  ```
  Known breaches
    shop.inventory -> shop.orders (1 edges)
    shop.reporting -> shop.payments (1 edges)

  0 new, 0 stale, 2 known (likec4 1.60.0 from plugin)
  ```

- Reviews: self-review and independent audit passed. Owner: [ARCH-APPROVED].

## Rule map

- BR-1 → `shop.checkout`
- BR-2 → `shop.refunds`
- BR-3 → `shop.reporting`
- BR-4 → `shop.orders`
- BR-5 → `shop.events`

## Cross-cutting decisions

### Order event format

- Owning element: `shop.events`.
- Bound elements: `shop.orders`, `shop.checkout`, `shop.refunds`, `shop.reporting`.
- Capabilities: checkout, refunds, reporting.
- Obligations: every order change emits one event (BR-4). Every event carries the order id and a sequence number, and consumers ignore an event already seen (BR-5).
- Compatibility: changes are additive only. Removing or renaming anything is a new format version that every bound element adopts together.

## Baseline coverage

Whole repository (10 modules, 8 groups, at or under the small-repo limits).

- Groups: `shop.api`, `shop.jobs`, `shop.checkout`, `shop.refunds`, `shop.reporting`, `shop.orders`, `shop.inventory`, `shop.payments`, all added by the 2026-11-02 baseline run.
- Edge nodes: none.

## Unmapped modules

None.
