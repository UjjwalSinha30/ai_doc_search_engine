"""Fix document file_hash constraint to be composite with user_id

Revision ID: 001
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old unique constraint on file_hash only
    op.drop_constraint('ix_documents_file_hash', 'documents', type_='unique')
    
    # Add the new composite unique constraint on (file_hash, user_id)
    op.create_unique_constraint('uix_filehash_userid', 'documents', ['file_hash', 'user_id'])


def downgrade() -> None:
    # Remove the composite constraint
    op.drop_constraint('uix_filehash_userid', 'documents', type_='unique')
    
    # Restore the old constraint
    op.create_unique_constraint('ix_documents_file_hash', 'documents', ['file_hash'])
