"""Demo knowledge base seeding for local development and live demonstrations."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

log = logging.getLogger(__name__)

DEMO_CHUNKS = [
    # Redis Caching - Technical Document
    {
        "chunk_id": "chunk_doc_redis_01",
        "document_id": "doc_adr_042",
        "source_id": "src_documents",
        "source_type": "document",
        "original_record_id": "adr-042",
        "chunk_index": 0,
        "title": "Architecture Decision Record ADR-042: Distributed Caching Tier",
        "source_reference": "docs/architecture/adr-042-redis-caching.md",
        "text": (
            "Official Architecture Decision Record ADR-042: Redis caching was introduced because "
            "database read latency exceeded acceptable SLA limits (p99 read latency exceeded 450ms "
            "against the target SLA of <50ms). The Redis cluster serves as an in-memory cache for "
            "user session data and frequently accessed tenant configurations, reducing PostgreSQL read pressure by 78%."
        ),
        "authority_level": 0.85,
        "authority_basis": "approved documentation is highly authoritative",
        "status": "approved",
        "created_at": "2024-03-15T10:00:00Z",
        "updated_at": "2024-03-15T10:00:00Z",
    },
    # Redis Caching - Engineering Conversation
    {
        "chunk_id": "chunk_conv_redis_01",
        "document_id": "conv_slack_redis_01",
        "source_id": "src_conversations",
        "source_type": "conversation",
        "original_record_id": "slack-backend-202403",
        "chunk_index": 0,
        "title": "Slack #backend-architecture: Cache Invalidation & Cluster Deployment",
        "source_reference": "slack/backend-architecture/2024-03-thread-cache.json",
        "text": (
            "Sarah (Staff Architect): We completed the deployment of the Redis read-through caching "
            "cluster today. As discussed in ADR-042, the primary driver was offloading heavy read "
            "traffic from the primary PostgreSQL cluster during peak morning traffic surges. Cache TTL "
            "is configured for 15 minutes with automated event-driven invalidation on tenant update mutations."
        ),
        "authority_level": 0.50,
        "authority_basis": "informal discussion unless marked as a decision",
        "status": "active",
        "created_at": "2024-03-18T14:30:00Z",
        "updated_at": "2024-03-18T14:30:00Z",
    },
    # Redis Caching - Ticket
    {
        "chunk_id": "chunk_ticket_redis_01",
        "document_id": "ticket_proj_1082",
        "source_id": "src_tickets",
        "source_type": "ticket",
        "original_record_id": "PROJ-1082",
        "chunk_index": 0,
        "title": "PROJ-1082: Implement Redis Session and Read-Through Cache Layer",
        "source_reference": "jira/tickets/PROJ-1082.json",
        "text": (
            "PROJ-1082 (Resolved): Implemented Redis distributed caching tier across production services. "
            "Benchmark results show p99 latency dropped from 460ms to 24ms, and database CPU utilization "
            "decreased from 84% to 22% under maximum synthetic load."
        ),
        "authority_level": 0.60,
        "authority_basis": "depends on ticket status",
        "status": "resolved",
        "created_at": "2024-03-20T09:15:00Z",
        "updated_at": "2024-03-22T17:00:00Z",
    },
    # Deployment Process - Technical Document
    {
        "chunk_id": "chunk_doc_deploy_01",
        "document_id": "doc_runbook_deploy",
        "source_id": "src_documents",
        "source_type": "document",
        "original_record_id": "runbook-deploy-v3",
        "chunk_index": 0,
        "title": "Production Deployment Runbook v3.2: Automated Canary Rollouts",
        "source_reference": "docs/devops/deployment-runbook-v3.md",
        "text": (
            "Official Deployment Runbook v3.2: The latest deployment process utilizes automated Kubernetes "
            "canary rollouts managed by ArgoCD and GitHub Actions CI/CD workflows. Every merge to main "
            "automatically triggers end-to-end integration tests, builds multi-arch container images, and "
            "initiates a 10% canary traffic rollout for 30 minutes with automated Prometheus metric health checks before promoting to 100%."
        ),
        "authority_level": 0.85,
        "authority_basis": "approved documentation is highly authoritative",
        "status": "approved",
        "created_at": "2024-05-10T08:00:00Z",
        "updated_at": "2024-05-10T08:00:00Z",
    },
    # Deployment Process - Engineering Conversation
    {
        "chunk_id": "chunk_conv_deploy_01",
        "document_id": "conv_slack_devops_01",
        "source_id": "src_conversations",
        "source_type": "conversation",
        "original_record_id": "slack-devops-202405",
        "chunk_index": 0,
        "title": "Slack #devops: Migration from Blue-Green to Canary Rollouts",
        "source_reference": "slack/devops/2024-05-canary-migration.json",
        "text": (
            "Alex (DevOps Lead): Team reminder that manual SSH deployments and legacy blue-green scripts "
            "have been completely deprecated. All deployments must follow the v3.2 automated canary pipeline "
            "via GitHub Actions. If a rollback is needed, trigger the rollback workflow in GitHub Actions or execute 'argocd app rollback quorix-prod'."
        ),
        "authority_level": 0.50,
        "authority_basis": "informal discussion unless marked as a decision",
        "status": "active",
        "created_at": "2024-05-12T11:20:00Z",
        "updated_at": "2024-05-12T11:20:00Z",
    },
    # Authentication - Technical Document
    {
        "chunk_id": "chunk_doc_auth_01",
        "document_id": "doc_auth_spec",
        "source_id": "src_documents",
        "source_type": "document",
        "original_record_id": "auth-spec-v2",
        "chunk_index": 0,
        "title": "Security Architecture Specification: Authentication & Authorization",
        "source_reference": "docs/security/auth-spec-v2.md",
        "text": (
            "Official Security Spec: Authentication is implemented using OAuth 2.0 and OpenID Connect (OIDC) protocols. "
            "The API Gateway issues short-lived RS256-signed JWT access tokens with a 15-minute expiration time. "
            "Sliding-window refresh tokens are stored in secure, HttpOnly, SameSite=Strict cookies with encrypted database back-channel rotation."
        ),
        "authority_level": 0.85,
        "authority_basis": "approved documentation is highly authoritative",
        "status": "approved",
        "created_at": "2024-04-01T12:00:00Z",
        "updated_at": "2024-04-01T12:00:00Z",
    },
    # Database Sharding - Technical Document
    {
        "chunk_id": "chunk_doc_sharding_01",
        "document_id": "doc_scaling_guide",
        "source_id": "src_documents",
        "source_type": "document",
        "original_record_id": "database-scaling",
        "chunk_index": 0,
        "title": "Data Architecture Guidelines: PostgreSQL Storage & Scaling",
        "source_reference": "docs/architecture/database-scaling.md",
        "text": (
            "Architecture Overview: Database sharding is NOT currently supported. The system relies on a single "
            "primary PostgreSQL instance with read replicas and connection pooling via PgBouncer. Sharding across "
            "customer tenants is scheduled for Phase 3 exploration in Q4 roadmap."
        ),
        "authority_level": 0.85,
        "authority_basis": "approved documentation is highly authoritative",
        "status": "approved",
        "created_at": "2024-04-15T09:00:00Z",
        "updated_at": "2024-04-15T09:00:00Z",
    },
]


def ensure_demo_data_seeded(client: QdrantClient, embedder: Any, collection: str = "quorix_chunks") -> None:
    """Seed benchmark knowledge chunks if the collection is empty."""
    try:
        if client.collection_exists(collection):
            count = client.count(collection, exact=True).count
            if count > 0:
                return

        # Generate embeddings first to match vector dimension exactly
        texts = [f"{c['title']} ({c['source_type']})\n{c['text']}" for c in DEMO_CHUNKS]
        vectors = embedder.embed_documents(texts)
        if not vectors or not vectors[0]:
            return
        dim = len(vectors[0])

        if not client.collection_exists(collection):
            client.create_collection(
                collection_name=collection,
                vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
            )

        # Upsert points
        points = []
        for idx, (chunk, vec) in enumerate(zip(DEMO_CHUNKS, vectors)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))
            points.append(
                qm.PointStruct(
                    id=point_id,
                    vector=vec,
                    payload=chunk,
                )
            )

        client.upsert(collection_name=collection, points=points, wait=True)
        log.info("Successfully seeded %d demo chunks into collection %s", len(points), collection)
    except Exception as exc:
        log.warning("Could not seed demo knowledge base into collection %s: %s", collection, exc)
