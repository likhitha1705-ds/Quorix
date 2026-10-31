---
id: DOC-009
title: Catalog Caching Improvements Proposal
author: Priya Raman
created_at: 2026-08-18T09:00:00Z
updated_at: 2026-08-18T09:00:00Z
status: draft
version: 0.2
tags: [redis, proposal]
---
# Catalog Caching Improvements (Draft)

This draft proposes raising the catalog cache TTL to 1200 seconds and adding a second Redis replica. It has not been reviewed and was not adopted; the team chose a smaller change in CONV-009.

## Open questions
Memory cost of a longer TTL is not yet measured.
