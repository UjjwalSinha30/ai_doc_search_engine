"""add document processing status

Revision ID: 942eb4a13b50
Revises: 002_add_document_indexes
Create Date: 2026-10-09 20:24:28.170893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '942eb4a13b50'
down_revision: Union[str, Sequence[str], None] = '002_add_document_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("documents", sa.Column("status", sa.String(length=20), nullable=True))
    op.add_column("documents", sa.Column("error_message", sa.String(length=500), nullable=True))
    op.create_index("ix_documents_status", "documents", ["status"])
    op.execute("UPDATE documents SET status = 'indexed' WHERE status IS NULL")
    

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_column("documents", "error_message")
    op.drop_column("documents", "status")
