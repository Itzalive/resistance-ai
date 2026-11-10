# Epic: order events

Status: [EPIC-APPROVED] 2026-11-01

## Capabilities

| Capability | MoSCoW | Summary |
|---|---|---|
| checkout | Must | A shopper pays for a basket and one order is written. |
| refunds | Must | A paid order is partly or fully refunded. |
| reporting | Must | A daily report sums payment totals per day. |

## Shared need

All three capabilities depend on one order-event format: checkout, refunds and reporting each produce or consume the same events about an order.

## Business rules

- BR-1 (checkout): a checkout writes exactly one order.
- BR-2 (refunds): a refund never exceeds the order's paid total.
- BR-3 (reporting): reporting reads payment totals only through order events, never from payments directly.
- BR-4 (all three): every change to an order, from the API or the nightly job, emits one order event.
- BR-5 (all three): every order event carries the order id and a sequence number, and a consumer ignores an event it has already seen.

## Decision log
