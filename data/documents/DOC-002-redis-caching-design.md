---
id: DOC-002
title: Redis Caching Design
author: Marcus Lee
created_at: 2026-02-18T10:00:00Z
updated_at: 2026-03-05T14:30:00Z
status: approved
version: 1.1
tags: [redis, caching, design]
---
# Redis Caching Design

## Pattern
nova-catalog uses the cache-aside pattern: read from Redis first, fall back to PostgreSQL on a miss, then populate the cache. This was chosen over write-through in CONV-002.

## Configuration
- Catalog cache TTL: 300 seconds
- Session cache TTL: 1800 seconds
- Eviction policy: allkeys-lru
- Max memory: 512 MB
- Key format: `catalog:{product_id}` and `session:{session_id}`

## Invalidation
Product updates delete the matching `catalog:{product_id}` key. Bulk imports flush the `catalog:*` namespace.
