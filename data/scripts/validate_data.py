"""Post-ingestion validation checks for support_kb and the Olist star schema.

Run after load_support_kb.py and build_star_schema.py. Exits non-zero and
prints every failure if the data looks wrong, instead of failing silently.

Usage:
    python data/scripts/validate_data.py
"""
import sys

from sqlalchemy import text

import _pathsetup  # noqa: F401  (adds backend/ to sys.path)

from app.db.session import SessionLocal

MIN_SUPPORT_KB_ROWS = 1000
MIN_OLIST_ORDERS = 1000

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def row_count(db, table: str) -> int:
    return db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()


def null_count(db, table: str, column: str) -> int:
    return db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")).scalar_one()


def orphan_count(db, child_table: str, child_column: str, parent_table: str, parent_column: str) -> int:
    query = text(
        f"SELECT COUNT(*) FROM {child_table} c "
        f"LEFT JOIN {parent_table} p ON c.{child_column} = p.{parent_column} "
        f"WHERE p.{parent_column} IS NULL"
    )
    return db.execute(query).scalar_one()


def main() -> None:
    db = SessionLocal()
    try:
        # Row counts
        support_kb_count = row_count(db, "support_kb")
        check(
            support_kb_count >= MIN_SUPPORT_KB_ROWS,
            f"support_kb has only {support_kb_count} rows, expected at least {MIN_SUPPORT_KB_ROWS}",
        )

        orders_count = row_count(db, "fact_orders")
        check(
            orders_count >= MIN_OLIST_ORDERS,
            f"fact_orders has only {orders_count} rows, expected at least {MIN_OLIST_ORDERS}",
        )

        for table in ["dim_customers", "dim_products", "dim_sellers", "fact_order_items", "fact_payments", "fact_reviews"]:
            count = row_count(db, table)
            check(count > 0, f"{table} is empty")

        # Null checks on required columns
        for table, column in [
            ("support_kb", "instruction"),
            ("support_kb", "response"),
            ("fact_orders", "order_status"),
            ("fact_orders", "customer_id"),
            ("fact_order_items", "price"),
            ("fact_payments", "payment_value"),
        ]:
            nulls = null_count(db, table, column)
            check(nulls == 0, f"{table}.{column} has {nulls} unexpected null values")

        # Foreign key integrity
        for child_table, child_column, parent_table, parent_column in [
            ("fact_orders", "customer_id", "dim_customers", "customer_id"),
            ("fact_order_items", "order_id", "fact_orders", "order_id"),
            ("fact_order_items", "product_id", "dim_products", "product_id"),
            ("fact_order_items", "seller_id", "dim_sellers", "seller_id"),
            ("fact_payments", "order_id", "fact_orders", "order_id"),
            ("fact_reviews", "order_id", "fact_orders", "order_id"),
        ]:
            orphans = orphan_count(db, child_table, child_column, parent_table, parent_column)
            check(
                orphans == 0,
                f"{child_table}.{child_column} has {orphans} rows with no matching {parent_table}.{parent_column}",
            )
    finally:
        db.close()

    if failures:
        print("data validation FAILED:", file=sys.stderr)
        for message in failures:
            print(f"  - {message}", file=sys.stderr)
        raise SystemExit(1)

    print("data validation passed: row counts, null checks, and foreign key integrity are all clean")


if __name__ == "__main__":
    main()
