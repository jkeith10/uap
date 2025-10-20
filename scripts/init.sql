-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create UAP database schema
CREATE SCHEMA IF NOT EXISTS uap;

-- World state table
CREATE TABLE IF NOT EXISTS uap.world_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Memory streams table
CREATE TABLE IF NOT EXISTS uap.memory_streams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id VARCHAR(255) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    intent JSONB NOT NULL,
    context JSONB,
    result JSONB,
    confidence FLOAT,
    next_action VARCHAR(255),
    granularity VARCHAR(50) NOT NULL, -- task, agent, organization
    retention_policy VARCHAR(50) NOT NULL, -- ephemeral, archived, permanent
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Action graphs table
CREATE TABLE IF NOT EXISTS uap.action_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    definition JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Node capabilities table
CREATE TABLE IF NOT EXISTS uap.node_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    capabilities JSONB NOT NULL,
    fingerprint JSONB NOT NULL,
    cost_weight FLOAT DEFAULT 1.0,
    latency_weight FLOAT DEFAULT 1.0,
    confidence_weight FLOAT DEFAULT 1.0,
    performance_history JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reflection reports table
CREATE TABLE IF NOT EXISTS uap.reflection_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id VARCHAR(255) NOT NULL UNIQUE,
    actor VARCHAR(255) NOT NULL,
    intent JSONB NOT NULL,
    context JSONB,
    result JSONB,
    confidence FLOAT,
    next_action VARCHAR(255),
    evaluation JSONB,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_world_state_key ON uap.world_state(key);
CREATE INDEX IF NOT EXISTS idx_memory_streams_stream_id ON uap.memory_streams(stream_id);
CREATE INDEX IF NOT EXISTS idx_memory_streams_actor ON uap.memory_streams(actor);
CREATE INDEX IF NOT EXISTS idx_memory_streams_granularity ON uap.memory_streams(granularity);
CREATE INDEX IF NOT EXISTS idx_memory_streams_retention ON uap.memory_streams(retention_policy);
CREATE INDEX IF NOT EXISTS idx_memory_streams_created_at ON uap.memory_streams(created_at);
CREATE INDEX IF NOT EXISTS idx_action_graphs_graph_id ON uap.action_graphs(graph_id);
CREATE INDEX IF NOT EXISTS idx_node_capabilities_node_id ON uap.node_capabilities(node_id);
CREATE INDEX IF NOT EXISTS idx_node_capabilities_active ON uap.node_capabilities(is_active);
CREATE INDEX IF NOT EXISTS idx_reflection_reports_report_id ON uap.reflection_reports(report_id);
CREATE INDEX IF NOT EXISTS idx_reflection_reports_actor ON uap.reflection_reports(actor);

-- Create vector index for semantic search (will be populated by application)
CREATE INDEX IF NOT EXISTS idx_memory_streams_intent_vector ON uap.memory_streams 
USING ivfflat ((intent::vector)) WITH (lists = 100);
