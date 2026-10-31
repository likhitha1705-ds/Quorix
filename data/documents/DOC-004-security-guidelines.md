---
id: DOC-004
title: Security Guidelines
author: Aisha Khan
created_at: 2026-03-10T09:00:00Z
updated_at: 2026-05-30T16:00:00Z
status: approved
version: 2.0
tags: [security, auth]
---
# Security Guidelines

## Access tokens
Access tokens expire after 60 minutes. Clients must use refresh tokens (see CONV-012) to obtain new access tokens. Refresh tokens expire after 30 days.

## Secrets
Secrets are stored in the cluster secret manager and never committed to source control. API keys are hashed at rest.

## Transport
All traffic uses TLS 1.2 or newer. Internal service traffic uses mTLS.
