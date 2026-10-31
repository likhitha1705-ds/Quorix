---
id: DOC-005
title: Service Configuration Reference
author: Marcus Lee
created_at: 2026-04-15T09:00:00Z
updated_at: 2026-06-20T12:00:00Z
status: approved
version: 2.0
tags: [configuration, redis, database]
---
# Service Configuration Reference

## nova-catalog
- `CATALOG_CACHE_TTL_SECONDS`: 600
- `SESSION_CACHE_TTL_SECONDS`: 1800
- `REDIS_MAX_MEMORY_MB`: 512

## Database
- `DB_POOL_SIZE`: 20 (raised from 10, see TKT-108)
- `DB_POOL_TIMEOUT_SECONDS`: 30

## nova-api
- `RATE_LIMIT_DEFAULT_PER_MINUTE`: 200
- `RATE_LIMIT_PARTNER_PER_MINUTE`: 500
