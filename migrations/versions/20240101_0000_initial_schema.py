"""Initial schema with all UAP tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create intents table
    op.create_table(
        'intents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('context', postgresql.JSONB, nullable=True),
        sa.Column('priority', sa.Integer, nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    
    # Create action_graphs table
    op.create_table(
        'action_graphs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('nodes', postgresql.JSONB, nullable=False),
        sa.Column('edges', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    
    # Create memory_streams table
    op.create_table(
        'memory_streams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('granularity', sa.String(50), nullable=False),
        sa.Column('entries', postgresql.JSONB, nullable=False),
        sa.Column('vector_embedding', postgresql.VECTOR(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    
    # Create reflection_reports table
    op.create_table(
        'reflection_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('evaluations', postgresql.JSONB, nullable=False),
        sa.Column('score', sa.Float, nullable=True),
        sa.Column('feedback', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    
    # Create world_state table
    op.create_table(
        'world_state',
        sa.Column('key', sa.String(255), primary_key=True),
        sa.Column('value', postgresql.JSONB, nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    
    # Create nodes table (for routing)
    op.create_table(
        'nodes',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('capabilities', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('cost_weight', sa.Float, nullable=False, default=1.0),
        sa.Column('latency_weight', sa.Float, nullable=False, default=1.0),
        sa.Column('confidence_weight', sa.Float, nullable=False, default=1.0),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    
    # Create routing_history table
    op.create_table(
        'routing_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('intent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', sa.String(255), nullable=False),
        sa.Column('decision_data', postgresql.JSONB, nullable=False),
        sa.Column('performance_score', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('data', postgresql.JSONB, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_intents_created_at', 'intents', ['created_at'])
    op.create_index('idx_intents_type', 'intents', ['type'])
    op.create_index('idx_action_graphs_status', 'action_graphs', ['status'])
    op.create_index('idx_action_graphs_created_at', 'action_graphs', ['created_at'])
    op.create_index('idx_memory_streams_granularity', 'memory_streams', ['granularity'])
    op.create_index('idx_memory_streams_created_at', 'memory_streams', ['created_at'])
    op.create_index('idx_reflection_reports_type', 'reflection_reports', ['type'])
    op.create_index('idx_reflection_reports_created_at', 'reflection_reports', ['created_at'])
    op.create_index('idx_world_state_updated_at', 'world_state', ['updated_at'])
    op.create_index('idx_nodes_status', 'nodes', ['status'])
    op.create_index('idx_routing_history_intent_id', 'routing_history', ['intent_id'])
    op.create_index('idx_routing_history_node_id', 'routing_history', ['node_id'])
    op.create_index('idx_routing_history_created_at', 'routing_history', ['created_at'])
    op.create_index('idx_events_type', 'events', ['type'])
    op.create_index('idx_events_timestamp', 'events', ['timestamp'])
    
    # Create vector index for similarity search
    op.execute('''
        CREATE INDEX idx_memory_streams_vector 
        ON memory_streams 
        USING ivfflat (vector_embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_memory_streams_vector')
    op.drop_index('idx_events_timestamp')
    op.drop_index('idx_events_type')
    op.drop_index('idx_routing_history_created_at')
    op.drop_index('idx_routing_history_node_id')
    op.drop_index('idx_routing_history_intent_id')
    op.drop_index('idx_nodes_status')
    op.drop_index('idx_world_state_updated_at')
    op.drop_index('idx_reflection_reports_created_at')
    op.drop_index('idx_reflection_reports_type')
    op.drop_index('idx_memory_streams_created_at')
    op.drop_index('idx_memory_streams_granularity')
    op.drop_index('idx_action_graphs_created_at')
    op.drop_index('idx_action_graphs_status')
    op.drop_index('idx_intents_type')
    op.drop_index('idx_intents_created_at')
    
    # Drop tables
    op.drop_table('events')
    op.drop_table('routing_history')
    op.drop_table('nodes')
    op.drop_table('world_state')
    op.drop_table('reflection_reports')
    op.drop_table('memory_streams')
    op.drop_table('action_graphs')
    op.drop_table('intents')
    
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')

