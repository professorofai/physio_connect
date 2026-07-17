"""Improve database design with relationships, timestamps, and stronger constraints."""

from app.utils.schema_migration import ensure_database_schema


def upgrade():
    ensure_database_schema()


def downgrade():
    raise NotImplementedError("Downgrade is not supported for this schema migration.")
