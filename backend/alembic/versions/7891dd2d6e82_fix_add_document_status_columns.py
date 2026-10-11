"""fix add document status columns

Revision ID: 7891dd2d6e82
Revises: 942eb4a13b50
Create Date: 2026-10-10 11:43:24.320302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7891dd2d6e82'
down_revision: Union[str, Sequence[str], None] = '942eb4a13b50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("documents")}
    indexes = {idx["name"] for idx in inspector.get_indexes("documents")}

    if "status" not in columns:
        op.add_column("documents", sa.Column("status", sa.String(length=20), nullable=True))

    if "error_message" not in columns:
        op.add_column("documents", sa.Column("error_message", sa.String(length=500), nullable=True))

    if "ix_documents_status" not in indexes:
        op.create_index("ix_documents_status", "documents", ["status"])

    op.execute("UPDATE documents SET status = 'indexed' WHERE status IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("documents")}
    indexes = {idx["name"] for idx in inspector.get_indexes("documents")}

    if "ix_documents_status" in indexes:
        op.drop_index("ix_documents_status", table_name="documents")

    if "error_message" in columns:
        op.drop_column("documents", "error_message")

    if "status" in columns:
        op.drop_column("documents", "status")
