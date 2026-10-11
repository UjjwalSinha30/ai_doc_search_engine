"""Add document lookup indexes

Revision ID: 002_add_document_indexes
Revises: 001
Create Date: 2026-10-08
"""

from alembic import op
from sqlalchemy import inspect

revision = "002_add_document_indexes"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    indexes = {idx["name"] for idx in inspector.get_indexes("documents")}

    if "ix_documents_user_id" not in indexes:
        op.create_index("ix_documents_user_id", "documents", ["user_id"], unique=False)

    if "ix_documents_user_file_hash" not in indexes:
        op.create_index(
            "ix_documents_user_file_hash",
            "documents",
            ["user_id", "file_hash"],
            unique=False,
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    indexes = {idx["name"] for idx in inspector.get_indexes("documents")}

    if "ix_documents_user_file_hash" in indexes:
        op.drop_index("ix_documents_user_file_hash", table_name="documents")

    if "ix_documents_user_id" in indexes:
        op.drop_index("ix_documents_user_id", table_name="documents")
