-- TrendsQL-KG Database Schema
-- PostgreSQL schema for trend data analysis with Knowledge Graph support

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension (optional)
CREATE EXTENSION IF NOT EXISTS "vector";

-- Exploding Topics table
CREATE TABLE IF NOT EXISTS exploding_topics (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    category TEXT,
    source TEXT DEFAULT 'exploding',
    first_seen_date DATE,
    growth_score NUMERIC,
    popularity_score NUMERIC,
    region TEXT,             -- e.g. 'US','IN', or null
    url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Google Trends Interest Over Time table
CREATE TABLE IF NOT EXISTS gt_interest_over_time (
    id BIGSERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    date DATE NOT NULL,
    interest INT NOT NULL,
    geo TEXT,                -- 'US','IN', etc
    category INT,            -- Google Trends category code
    gprop TEXT,              -- '', 'news', 'images', 'youtube', 'froogle'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Google Trends Related Topics table
CREATE TABLE IF NOT EXISTS gt_related_topics (
    id BIGSERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    related_topic TEXT NOT NULL,
    type TEXT,               -- 'rising'|'top'
    value INT,
    geo TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge Graph node summaries table (for vector search)
CREATE TABLE IF NOT EXISTS kg_node_summaries (
    id BIGSERIAL PRIMARY KEY,
    node_id TEXT NOT NULL,           -- Neo4j node ID
    node_label TEXT NOT NULL,        -- Topic, Keyword, Category, Region
    node_key TEXT NOT NULL,          -- Primary key value
    summary TEXT NOT NULL,           -- LLM-generated summary
    embedding VECTOR(3072),          -- Vector embedding of summary
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge Graph community summaries table
CREATE TABLE IF NOT EXISTS kg_community_summaries (
    id BIGSERIAL PRIMARY KEY,
    community_type TEXT NOT NULL,    -- 'category', 'region', 'cluster'
    community_key TEXT NOT NULL,     -- category name, region code, etc.
    summary TEXT NOT NULL,           -- LLM-generated community summary
    node_count INT NOT NULL,         -- Number of nodes in community
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_exploding_topics_topic ON exploding_topics(topic);
CREATE INDEX IF NOT EXISTS idx_exploding_topics_region ON exploding_topics(region);
CREATE INDEX IF NOT EXISTS idx_exploding_topics_category ON exploding_topics(category);
CREATE INDEX IF NOT EXISTS idx_exploding_topics_growth_score ON exploding_topics(growth_score DESC);
CREATE INDEX IF NOT EXISTS idx_exploding_topics_popularity_score ON exploding_topics(popularity_score DESC);
CREATE INDEX IF NOT EXISTS idx_exploding_topics_first_seen_date ON exploding_topics(first_seen_date);
CREATE INDEX IF NOT EXISTS idx_exploding_topics_created_at ON exploding_topics(created_at);

CREATE INDEX IF NOT EXISTS idx_gt_interest_over_time_keyword ON gt_interest_over_time(keyword);
CREATE INDEX IF NOT EXISTS idx_gt_interest_over_time_date ON gt_interest_over_time(date);
CREATE INDEX IF NOT EXISTS idx_gt_interest_over_time_geo ON gt_interest_over_time(geo);
CREATE INDEX IF NOT EXISTS idx_gt_interest_over_time_keyword_date ON gt_interest_over_time(keyword, date);
CREATE INDEX IF NOT EXISTS idx_gt_interest_over_time_interest ON gt_interest_over_time(interest DESC);

CREATE INDEX IF NOT EXISTS idx_gt_related_topics_keyword ON gt_related_topics(keyword);
CREATE INDEX IF NOT EXISTS idx_gt_related_topics_type ON gt_related_topics(type);
CREATE INDEX IF NOT EXISTS idx_gt_related_topics_geo ON gt_related_topics(geo);
CREATE INDEX IF NOT EXISTS idx_gt_related_topics_value ON gt_related_topics(value DESC);

-- Knowledge Graph indexes
CREATE INDEX IF NOT EXISTS idx_kg_node_summaries_node_id ON kg_node_summaries(node_id);
CREATE INDEX IF NOT EXISTS idx_kg_node_summaries_label ON kg_node_summaries(node_label);
CREATE INDEX IF NOT EXISTS idx_kg_node_summaries_key ON kg_node_summaries(node_key);
CREATE INDEX IF NOT EXISTS idx_kg_node_summaries_created_at ON kg_node_summaries(created_at);

CREATE INDEX IF NOT EXISTS idx_kg_community_summaries_type ON kg_community_summaries(community_type);
CREATE INDEX IF NOT EXISTS idx_kg_community_summaries_key ON kg_community_summaries(community_key);
CREATE INDEX IF NOT EXISTS idx_kg_community_summaries_created_at ON kg_community_summaries(created_at);

-- Vector indexes (if pgvector is enabled)
CREATE INDEX IF NOT EXISTS idx_kg_node_summaries_embedding ON kg_node_summaries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Unique constraints for upsert operations
CREATE UNIQUE INDEX IF NOT EXISTS idx_exploding_topics_unique ON exploding_topics(topic, COALESCE(region, ''));
CREATE UNIQUE INDEX IF NOT EXISTS idx_gt_interest_over_time_unique ON gt_interest_over_time(keyword, date, COALESCE(geo, ''), COALESCE(gprop, ''), COALESCE(category, 0));
CREATE UNIQUE INDEX IF NOT EXISTS idx_gt_related_topics_unique ON gt_related_topics(keyword, related_topic, type, COALESCE(geo, ''));
CREATE UNIQUE INDEX IF NOT EXISTS idx_kg_node_summaries_unique ON kg_node_summaries(node_id, node_label);
CREATE UNIQUE INDEX IF NOT EXISTS idx_kg_community_summaries_unique ON kg_community_summaries(community_type, community_key);

-- Comments for documentation
COMMENT ON TABLE exploding_topics IS 'Exploding topics data from various sources';
COMMENT ON TABLE gt_interest_over_time IS 'Google Trends interest over time data';
COMMENT ON TABLE gt_related_topics IS 'Google Trends related topics data';
COMMENT ON TABLE kg_node_summaries IS 'Knowledge Graph node summaries with embeddings for vector search';
COMMENT ON TABLE kg_community_summaries IS 'Knowledge Graph community summaries for GraphRAG';

COMMENT ON COLUMN exploding_topics.topic IS 'The trending topic name';
COMMENT ON COLUMN exploding_topics.growth_score IS 'Growth score indicating trend velocity';
COMMENT ON COLUMN exploding_topics.popularity_score IS 'Overall popularity score';
COMMENT ON COLUMN exploding_topics.region IS 'Geographic region (US, IN, etc.) or null for global';

COMMENT ON COLUMN gt_interest_over_time.keyword IS 'The search keyword';
COMMENT ON COLUMN gt_interest_over_time.interest IS 'Interest score (0-100)';
COMMENT ON COLUMN gt_interest_over_time.geo IS 'Geographic location code';
COMMENT ON COLUMN gt_interest_over_time.gprop IS 'Google property (news, images, youtube, froogle)';

COMMENT ON COLUMN kg_node_summaries.node_id IS 'Neo4j node identifier';
COMMENT ON COLUMN kg_node_summaries.summary IS 'LLM-generated summary for vector search';
COMMENT ON COLUMN kg_node_summaries.embedding IS 'Vector embedding of the summary text';
