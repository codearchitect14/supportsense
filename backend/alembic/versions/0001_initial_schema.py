"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=32), nullable=False, unique=True),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "support_kb",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
    )
    op.create_index("ix_support_kb_category", "support_kb", ["category"])
    op.create_index("ix_support_kb_intent", "support_kb", ["intent"])
    op.execute(
        "CREATE INDEX ix_support_kb_embedding_hnsw ON support_kb "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("provider_used", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "dim_customers",
        sa.Column("customer_id", sa.String(length=32), primary_key=True),
        sa.Column("customer_unique_id", sa.String(length=32), nullable=False),
        sa.Column("customer_zip_code_prefix", sa.String(length=8), nullable=True),
        sa.Column("customer_city", sa.String(length=128), nullable=True),
        sa.Column("customer_state", sa.String(length=2), nullable=True),
    )
    op.create_index("ix_dim_customers_customer_unique_id", "dim_customers", ["customer_unique_id"])

    op.create_table(
        "dim_products",
        sa.Column("product_id", sa.String(length=32), primary_key=True),
        sa.Column("product_category_name", sa.String(length=128), nullable=True),
        sa.Column("product_weight_g", sa.Numeric(10, 2), nullable=True),
        sa.Column("product_length_cm", sa.Numeric(10, 2), nullable=True),
        sa.Column("product_height_cm", sa.Numeric(10, 2), nullable=True),
        sa.Column("product_width_cm", sa.Numeric(10, 2), nullable=True),
    )
    op.create_index("ix_dim_products_category", "dim_products", ["product_category_name"])

    op.create_table(
        "dim_sellers",
        sa.Column("seller_id", sa.String(length=32), primary_key=True),
        sa.Column("seller_zip_code_prefix", sa.String(length=8), nullable=True),
        sa.Column("seller_city", sa.String(length=128), nullable=True),
        sa.Column("seller_state", sa.String(length=2), nullable=True),
    )

    op.create_table(
        "fact_orders",
        sa.Column("order_id", sa.String(length=32), primary_key=True),
        sa.Column(
            "customer_id", sa.String(length=32), sa.ForeignKey("dim_customers.customer_id"), nullable=False
        ),
        sa.Column("order_status", sa.String(length=32), nullable=False),
        sa.Column("order_purchase_timestamp", sa.DateTime(), nullable=True),
        sa.Column("order_approved_at", sa.DateTime(), nullable=True),
        sa.Column("order_delivered_carrier_date", sa.DateTime(), nullable=True),
        sa.Column("order_delivered_customer_date", sa.DateTime(), nullable=True),
        sa.Column("order_estimated_delivery_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_fact_orders_customer_id", "fact_orders", ["customer_id"])
    op.create_index("ix_fact_orders_status", "fact_orders", ["order_status"])
    op.create_index("ix_fact_orders_purchase_ts", "fact_orders", ["order_purchase_timestamp"])

    op.create_table(
        "fact_order_items",
        sa.Column("order_id", sa.String(length=32), sa.ForeignKey("fact_orders.order_id"), primary_key=True),
        sa.Column("order_item_id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id", sa.String(length=32), sa.ForeignKey("dim_products.product_id"), nullable=False
        ),
        sa.Column("seller_id", sa.String(length=32), sa.ForeignKey("dim_sellers.seller_id"), nullable=False),
        sa.Column("shipping_limit_date", sa.DateTime(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("freight_value", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("ix_fact_order_items_product_id", "fact_order_items", ["product_id"])
    op.create_index("ix_fact_order_items_seller_id", "fact_order_items", ["seller_id"])

    op.create_table(
        "fact_payments",
        sa.Column("order_id", sa.String(length=32), sa.ForeignKey("fact_orders.order_id"), primary_key=True),
        sa.Column("payment_sequential", sa.Integer(), primary_key=True),
        sa.Column("payment_type", sa.String(length=32), nullable=False),
        sa.Column("payment_installments", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payment_value", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("ix_fact_payments_type", "fact_payments", ["payment_type"])

    op.create_table(
        "fact_reviews",
        sa.Column("review_id", sa.String(length=32), primary_key=True),
        sa.Column("order_id", sa.String(length=32), sa.ForeignKey("fact_orders.order_id"), nullable=False),
        sa.Column("review_score", sa.Integer(), nullable=False),
        sa.Column("review_comment_title", sa.Text(), nullable=True),
        sa.Column("review_comment_message", sa.Text(), nullable=True),
        sa.Column("review_creation_date", sa.DateTime(), nullable=True),
        sa.Column("review_answer_timestamp", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_fact_reviews_order_id", "fact_reviews", ["order_id"])
    op.create_index("ix_fact_reviews_score", "fact_reviews", ["review_score"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_action", "audit_log", ["action"])

    op.execute(
        "INSERT INTO roles (name) VALUES ('admin'), ('agent'), ('viewer') "
        "ON CONFLICT (name) DO NOTHING"
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("fact_reviews")
    op.drop_table("fact_payments")
    op.drop_table("fact_order_items")
    op.drop_table("fact_orders")
    op.drop_table("dim_sellers")
    op.drop_table("dim_products")
    op.drop_table("dim_customers")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.execute("DROP INDEX IF EXISTS ix_support_kb_embedding_hnsw")
    op.drop_table("support_kb")
    op.drop_table("users")
    op.drop_table("roles")
