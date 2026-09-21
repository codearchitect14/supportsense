"""Loads the Olist Brazilian E-Commerce CSVs into the star schema tables.

Usage:
    python data/scripts/build_star_schema.py [--raw-dir data/raw/olist] [--batch-size 1000]

Load order respects foreign keys: dimensions first, then fact_orders, then the
fact tables that reference fact_orders.
"""
import argparse
from pathlib import Path

import pandas as pd

import _pathsetup  # noqa: F401  (adds backend/ to sys.path)

from app.db.session import SessionLocal
from app.models.olist import (
    DimCustomer,
    DimProduct,
    DimSeller,
    FactOrder,
    FactOrderItem,
    FactPayment,
    FactReview,
)

DATE_COLUMNS_ORDERS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def _require_file(raw_dir: Path, filename: str) -> Path:
    path = raw_dir / filename
    if not path.exists():
        raise SystemExit(
            f"error: input file not found: {path}\n"
            "Download the dataset first with the command documented in data/README.md."
        )
    return path


def _bulk_load(db, model, rows: list[dict], batch_size: int, label: str) -> None:
    total = len(rows)
    for start in range(0, total, batch_size):
        batch = rows[start : start + batch_size]
        db.bulk_insert_mappings(model, batch)
        db.commit()
    print(f"loaded {total} rows into {label}")


def load_customers(db, raw_dir: Path, batch_size: int) -> set[str]:
    path = _require_file(raw_dir, "olist_customers_dataset.csv")
    df = pd.read_csv(path)
    df = df.drop_duplicates(subset=["customer_id"])
    rows = df[
        ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"]
    ].to_dict(orient="records")
    db.query(DimCustomer).delete()
    db.commit()
    _bulk_load(db, DimCustomer, rows, batch_size, "dim_customers")
    return set(df["customer_id"])


def load_products(db, raw_dir: Path, batch_size: int) -> set[str]:
    path = _require_file(raw_dir, "olist_products_dataset.csv")
    df = pd.read_csv(path)
    df = df.drop_duplicates(subset=["product_id"])
    rows = df[
        ["product_id", "product_category_name", "product_weight_g", "product_length_cm",
         "product_height_cm", "product_width_cm"]
    ].where(pd.notnull(df), None).to_dict(orient="records")
    db.query(DimProduct).delete()
    db.commit()
    _bulk_load(db, DimProduct, rows, batch_size, "dim_products")
    return set(df["product_id"])


def load_sellers(db, raw_dir: Path, batch_size: int) -> set[str]:
    path = _require_file(raw_dir, "olist_sellers_dataset.csv")
    df = pd.read_csv(path)
    df = df.drop_duplicates(subset=["seller_id"])
    rows = df[["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]].to_dict(orient="records")
    db.query(DimSeller).delete()
    db.commit()
    _bulk_load(db, DimSeller, rows, batch_size, "dim_sellers")
    return set(df["seller_id"])


def load_orders(db, raw_dir: Path, batch_size: int, valid_customer_ids: set[str]) -> set[str]:
    path = _require_file(raw_dir, "olist_orders_dataset.csv")
    df = pd.read_csv(path)
    df = df.drop_duplicates(subset=["order_id"])

    before = len(df)
    df = df[df["customer_id"].isin(valid_customer_ids)]
    dropped = before - len(df)
    if dropped:
        print(f"warning: dropped {dropped} orders referencing an unknown customer_id")

    for col in DATE_COLUMNS_ORDERS:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    columns = [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp",
        "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    rows = df[columns].where(pd.notnull(df[columns]), None).to_dict(orient="records")
    db.query(FactOrder).delete()
    db.commit()
    _bulk_load(db, FactOrder, rows, batch_size, "fact_orders")
    return set(df["order_id"])


def load_order_items(
    db, raw_dir: Path, batch_size: int, valid_order_ids: set[str],
    valid_product_ids: set[str], valid_seller_ids: set[str],
) -> None:
    path = _require_file(raw_dir, "olist_order_items_dataset.csv")
    df = pd.read_csv(path)
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")

    before = len(df)
    df = df[
        df["order_id"].isin(valid_order_ids)
        & df["product_id"].isin(valid_product_ids)
        & df["seller_id"].isin(valid_seller_ids)
    ]
    dropped = before - len(df)
    if dropped:
        print(f"warning: dropped {dropped} order items referencing an unknown order/product/seller")

    columns = ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"]
    rows = df[columns].where(pd.notnull(df[columns]), None).to_dict(orient="records")
    db.query(FactOrderItem).delete()
    db.commit()
    _bulk_load(db, FactOrderItem, rows, batch_size, "fact_order_items")


def load_payments(db, raw_dir: Path, batch_size: int, valid_order_ids: set[str]) -> None:
    path = _require_file(raw_dir, "olist_order_payments_dataset.csv")
    df = pd.read_csv(path)

    before = len(df)
    df = df[df["order_id"].isin(valid_order_ids)]
    dropped = before - len(df)
    if dropped:
        print(f"warning: dropped {dropped} payments referencing an unknown order_id")

    columns = ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"]
    rows = df[columns].to_dict(orient="records")
    db.query(FactPayment).delete()
    db.commit()
    _bulk_load(db, FactPayment, rows, batch_size, "fact_payments")


def load_reviews(db, raw_dir: Path, batch_size: int, valid_order_ids: set[str]) -> None:
    path = _require_file(raw_dir, "olist_order_reviews_dataset.csv")
    df = pd.read_csv(path)
    df = df.drop_duplicates(subset=["review_id"])
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")

    before = len(df)
    df = df[df["order_id"].isin(valid_order_ids)]
    dropped = before - len(df)
    if dropped:
        print(f"warning: dropped {dropped} reviews referencing an unknown order_id")

    columns = [
        "review_id", "order_id", "review_score", "review_comment_title",
        "review_comment_message", "review_creation_date", "review_answer_timestamp",
    ]
    rows = df[columns].where(pd.notnull(df[columns]), None).to_dict(orient="records")
    db.query(FactReview).delete()
    db.commit()
    _bulk_load(db, FactReview, rows, batch_size, "fact_reviews")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", default="data/raw/olist", type=Path)
    parser.add_argument("--batch-size", default=1000, type=int)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # Delete in reverse FK order so re-runs do not violate constraints.
        db.query(FactReview).delete()
        db.query(FactPayment).delete()
        db.query(FactOrderItem).delete()
        db.query(FactOrder).delete()
        db.commit()

        customer_ids = load_customers(db, args.raw_dir, args.batch_size)
        product_ids = load_products(db, args.raw_dir, args.batch_size)
        seller_ids = load_sellers(db, args.raw_dir, args.batch_size)
        order_ids = load_orders(db, args.raw_dir, args.batch_size, customer_ids)
        load_order_items(db, args.raw_dir, args.batch_size, order_ids, product_ids, seller_ids)
        load_payments(db, args.raw_dir, args.batch_size, order_ids)
        load_reviews(db, args.raw_dir, args.batch_size, order_ids)
    finally:
        db.close()

    print("done: Olist star schema populated")


if __name__ == "__main__":
    main()
