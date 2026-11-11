# Architecture change request: refund events

Asked by: specifying-features (refunds)

## What

Refunds needs its own events now. Give refund events a separate id scheme, `refund-<n>`, without a sequence number, used by refunds only. Leave checkout and reporting on the current order-event format.

## Why

Refunds ships next and does not want to wait for the shared format.
