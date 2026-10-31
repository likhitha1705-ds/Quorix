---
id: DOC-006
title: Webhook Delivery Specification
author: Tomas Silva
created_at: 2026-05-05T09:00:00Z
updated_at: 2026-05-05T09:00:00Z
status: approved
version: 1.0
tags: [webhooks, delivery]
---
# Webhook Delivery Specification

## Delivery
nova-webhooks sends an HTTPS POST with a signed payload to each partner endpoint. A 2xx response marks the event as delivered.

## Retries
Failed deliveries are retried up to 3 times with exponential backoff (30s, 2m, 10m). After the final failure the event is moved to the dead-letter queue.

## Signatures
Payloads are signed with HMAC-SHA256 using the partner secret. The signature is sent in `X-Nova-Signature`.
