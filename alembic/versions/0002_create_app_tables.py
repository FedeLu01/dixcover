"""create app tables

Revision ID: 0002_create_app_tables
Revises: 0001_initial
Create Date: 2025-12-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_create_app_tables'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Helper: create if not exists
    def create_if_missing(table_name, create_fn):
        if not inspector.has_table(table_name):
            create_fn()
        else:
            # table exists, skip
            pass

    # Alive subdomains
    create_if_missing('alive_subdomains', lambda: op.create_table(
        'alive_subdomains',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('subdomain', sa.String(length=1024), nullable=False, unique=True),
        sa.Column('probed_at', sa.DateTime, nullable=True),
        sa.Column('last_alive', sa.DateTime, nullable=True),
        sa.Column('status_code', sa.Integer, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
    ))

    # Domain requested
    create_if_missing('domain_requested', lambda: op.create_table(
        'domain_requested',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('domain', sa.String(length=1024), nullable=False),
        sa.Column('requested_at', sa.DateTime, nullable=False),
        sa.Column('time_to_zero', sa.DateTime, nullable=False),
        sa.Column('scheduled', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('requested_by', sa.String(length=512), nullable=True),
    ))

    # crtsh subdomains
    create_if_missing('crtsh_subdomain', lambda: op.create_table(
        'crtsh_subdomain',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('subdomain', sa.String(length=1024), nullable=True, unique=True),
        sa.Column('registered_on', sa.String(length=256), nullable=True),
        sa.Column('expires_on', sa.String(length=256), nullable=True),
    ))

    # otx subdomains
    create_if_missing('otx_subdomains', lambda: op.create_table(
        'otx_subdomains',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('address', sa.String(length=1024), nullable=True),
        sa.Column('subdomain', sa.String(length=1024), nullable=True, unique=True),
    ))

    # shodan subdomains
    create_if_missing('shodan_subdomain', lambda: op.create_table(
        'shodan_subdomain',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('subdomain', sa.String(length=1024), nullable=False, unique=True),
    ))

    # master subdomains
    create_if_missing('subdomains_master', lambda: op.create_table(
        'subdomains_master',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('subdomain', sa.String(length=1024), nullable=False, unique=True),
        sa.Column('sources', sa.JSON, nullable=False),
        sa.Column('last_alive', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    ))

    # virus total subdomains
    create_if_missing('virus_total_subdomain', lambda: op.create_table(
        'virus_total_subdomain',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('subdomain', sa.String(length=1024), nullable=True, unique=True),
    ))


def downgrade() -> None:
    op.drop_table('virus_total_subdomain')
    op.drop_table('subdomains_master')
    op.drop_table('shodan_subdomain')
    op.drop_table('otx_subdomains')
    op.drop_table('crtsh_subdomain')
    op.drop_table('domain_requested')
    op.drop_table('alive_subdomains')
