---
id: DOC-003
title: TechNova API Reference
author: Elena Petrova
created_at: 2026-03-01T09:00:00Z
updated_at: 2026-04-02T11:00:00Z
status: approved
version: 1.3
tags: [api, rate-limit, reference]
---
# TechNova API Reference

## Authentication
All requests require an API key in the `X-Nova-Key` header plus a bearer access token.

## Rate limiting
The default rate limit is 100 requests per minute per API key. Exceeding the limit returns HTTP 429 with a `Retry-After` header.

## Pagination
List endpoints accept `limit` (max 100) and `cursor`. Responses include `next_cursor` when more results exist.

## Errors
Errors use a JSON body with `code`, `message` and `request_id`.
