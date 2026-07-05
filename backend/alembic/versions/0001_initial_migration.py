"""Migração inicial: cria todas as tabelas do sistema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


license_type_enum = sa.Enum(
    "1_dia", "7_dias", "30_dias", "1_ano", "vitalicia", "customizada",
    name="licensetype",
)
license_status_enum = sa.Enum(
    "ativa", "expirada", "suspensa", "banida",
    name="licensestatus",
)


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("username", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_super_admin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "licenses",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("license_key", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("license_type", license_type_enum, nullable=False),
        sa.Column("status", license_status_enum, nullable=False),
        sa.Column("is_lifetime", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("use_hwid", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("hwid", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("last_ip", sa.String(64), nullable=True),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
        sa.Column("previous_login_at", sa.DateTime, nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime, nullable=True),
        sa.Column("last_version_used", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "login_history",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "license_id",
            sa.Integer,
            sa.ForeignKey("licenses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ip_address", sa.String(64), nullable=False),
        sa.Column("hwid", sa.String(255), nullable=True),
        sa.Column("version_used", sa.String(32), nullable=True),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("failure_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True, index=True),
    )

    op.create_table(
        "program_versions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("version", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column("changelog", sa.Text, nullable=True),
        sa.Column("download_url", sa.String(500), nullable=False),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.false(), index=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "maintenance",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.Column("updated_by", sa.String(64), nullable=True),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "license_id",
            sa.Integer,
            sa.ForeignKey("licenses.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("session_token", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("hwid", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("last_heartbeat_at", sa.DateTime, nullable=True, index=True),
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("key", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("value", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("sessions")
    op.drop_table("maintenance")
    op.drop_table("program_versions")
    op.drop_table("login_history")
    op.drop_table("licenses")
    op.drop_table("admins")
    license_status_enum.drop(op.get_bind(), checkfirst=True)
    license_type_enum.drop(op.get_bind(), checkfirst=True)
