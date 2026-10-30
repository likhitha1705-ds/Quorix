-- Migration 002: Add supported_topics column to knowledge_sources
ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS supported_topics TEXT[] DEFAULT '{}';

