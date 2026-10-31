---
id: DOC-001
title: TechNova Platform Architecture Overview
author: Priya Raman
created_at: 2026-02-10T09:00:00Z
updated_at: 2026-02-10T09:00:00Z
status: approved
version: 1.0
tags: [architecture, overview]
---
# TechNova Platform Architecture Overview

## Components
The TechNova Orders Platform consists of nova-api (FastAPI gateway), nova-catalog (product catalog service), nova-orders (order processing), and nova-webhooks (outbound webhook worker). All services run on Kubernetes and share a managed PostgreSQL 15 cluster.

## Caching
To reduce catalog latency, nova-catalog uses a Redis cache in front of PostgreSQL (introduced in TKT-101 after the discussion in CONV-001). The catalog cache TTL is 300 seconds. See DOC-002 for the caching design.

## Data flow
Clients call nova-api, which authenticates the request, applies rate limiting, and routes to the owning service. Order events are published to the webhook worker for delivery to partners.
