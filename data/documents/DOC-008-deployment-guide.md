---
id: DOC-008
title: Deployment Guide
author: Elena Petrova
created_at: 2026-03-20T09:00:00Z
updated_at: 2026-08-25T10:00:00Z
status: approved
version: 1.4
tags: [deployment, kubernetes]
---
# Deployment Guide

## Release process
Releases are built in CI, deployed to staging, and promoted to production after smoke tests pass. Production deploys use rolling updates with a maximum surge of 25 percent.

## Change freeze
No production deploys are allowed on Fridays after 14:00 UTC. Configuration-only changes follow the same rule.

## Rollback
Run `kubectl rollout undo` for the affected deployment, then confirm health checks pass.
