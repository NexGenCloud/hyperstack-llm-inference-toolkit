"""initial migrations

Revision ID: 86dacd76e074
Revises: 
Create Date: 2024-07-15 12:39:23.748605

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '86dacd76e074'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('api_key',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=True),
    sa.Column('api_key', sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(length=255), nullable=True),
    sa.Column('model_name', sa.String(length=255), nullable=True),
    sa.Column('allowed_rpm', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_api_key_api_key'), ['api_key'], unique=True)
        batch_op.create_index(batch_op.f('ix_api_key_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_api_key_user_id'), ['user_id'], unique=False)

    op.create_table('llm_models',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('llm_models', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_llm_models_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_llm_models_name'), ['name'], unique=True)

    op.create_table('metric',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('api_key_id', sa.Integer(), nullable=True),
    sa.Column('input', sa.Text(), nullable=True),
    sa.Column('created', sa.Integer(), nullable=True),
    sa.Column('model', sa.String(length=255), nullable=True),
    sa.Column('choices', sa.Text(), nullable=True),
    sa.Column('prompt_tokens', sa.Integer(), nullable=True),
    sa.Column('total_tokens', sa.Integer(), nullable=True),
    sa.Column('completion_tokens', sa.Integer(), nullable=True),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['api_key_id'], ['api_key.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('metric', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_metric_id'), ['id'], unique=False)

    op.create_table('replicas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('model_id', sa.Integer(), nullable=False),
    sa.Column('endpoint', sa.String(length=255), nullable=True),
    sa.Column('rate_limit', sa.Integer(), nullable=True),
    sa.Column('flavor_name', sa.String(length=255), nullable=True),
    sa.Column('vm_status', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('environment_name', sa.String(length=255), nullable=True),
    sa.Column('image_name', sa.String(length=255), nullable=True),
    sa.Column('assign_floating_ip', sa.Boolean(), nullable=True),
    sa.Column('run_command', sa.TEXT(), nullable=True),
    sa.Column('key_name', sa.String(length=255), nullable=True),
    sa.Column('vm_id', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['model_id'], ['llm_models.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('replicas', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_replicas_id'), ['id'], unique=False)

    op.create_table('replica_security_rules',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('replica_id', sa.Integer(), nullable=False),
    sa.Column('direction', sa.String(length=64), nullable=False),
    sa.Column('protocol', sa.String(length=64), nullable=False),
    sa.Column('ethertype', sa.String(length=64), nullable=False),
    sa.Column('remote_ip_prefix', sa.String(length=64), nullable=False),
    sa.Column('port_range_min', sa.Integer(), nullable=False),
    sa.Column('port_range_max', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['replica_id'], ['replicas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('replica_security_rules')
    with op.batch_alter_table('replicas', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_replicas_id'))

    op.drop_table('replicas')
    with op.batch_alter_table('metric', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_metric_id'))

    op.drop_table('metric')
    with op.batch_alter_table('llm_models', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_llm_models_name'))
        batch_op.drop_index(batch_op.f('ix_llm_models_id'))

    op.drop_table('llm_models')
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_api_key_user_id'))
        batch_op.drop_index(batch_op.f('ix_api_key_id'))
        batch_op.drop_index(batch_op.f('ix_api_key_api_key'))

    op.drop_table('api_key')
    # ### end Alembic commands ###
