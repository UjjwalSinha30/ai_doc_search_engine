"""Fix document file_hash constraint to be composite with user_id

Revision ID: 001
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    indexes = {idx["name"] for idx in inspector.get_indexes("documents")}
    unique_constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("documents")
    }

    # Older schemas may have this as either a unique constraint or an index.
    if "ix_documents_file_hash" in unique_constraints:
        op.drop_constraint("ix_documents_file_hash", "documents", type_="unique")
    elif "ix_documents_file_hash" in indexes:
        op.drop_index("ix_documents_file_hash", table_name="documents")

    if "uix_filehash_userid" not in unique_constraints:
        op.create_unique_constraint(
            "uix_filehash_userid",
            "documents",
            ["file_hash", "user_id"],
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    indexes = {idx["name"] for idx in inspector.get_indexes("documents")}
    unique_constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("documents")
    }

    if "uix_filehash_userid" in unique_constraints:
        op.drop_constraint("uix_filehash_userid", "documents", type_="unique")

    if "ix_documents_file_hash" not in unique_constraints and "ix_documents_file_hash" not in indexes:
        op.create_unique_constraint("ix_documents_file_hash", "documents", ["file_hash"])
