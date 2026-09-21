"""Loads the Bitext customer support dataset into the support_kb table.

Usage:
    python data/scripts/load_support_kb.py [--csv data/raw/support_kb.csv] [--batch-size 500]

Embeddings are left null here; they are populated separately by
data/scripts/generate_embeddings.py once the embedding service is built.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

import _pathsetup  # noqa: F401  (adds backend/ to sys.path)

from app.db.session import SessionLocal
from app.models.support_kb import SupportKB

REQUIRED_COLUMNS = ["instruction", "response", "category", "intent"]


def load_and_clean(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        print(f"error: input file not found: {csv_path}", file=sys.stderr)
        print("Download it first with the command documented in data/README.md.", file=sys.stderr)
        raise SystemExit(1)

    df = pd.read_csv(csv_path)

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        print(f"error: input file is missing required columns: {missing_columns}", file=sys.stderr)
        raise SystemExit(1)

    df = df[REQUIRED_COLUMNS].copy()
    for col in REQUIRED_COLUMNS:
        df[col] = df[col].astype(str).str.strip()

    before = len(df)
    df = df[(df["instruction"] != "") & (df["response"] != "")]
    df = df.drop_duplicates(subset=["instruction", "response"])
    after = len(df)
    print(f"loaded {before} rows, kept {after} after cleaning and deduplication")

    return df


def load_into_db(df: pd.DataFrame, batch_size: int) -> None:
    db = SessionLocal()
    try:
        existing = db.query(SupportKB).count()
        if existing > 0:
            print(f"support_kb already has {existing} rows; truncating before reload")
            db.query(SupportKB).delete()
            db.commit()

        rows = df.to_dict(orient="records")
        total = len(rows)
        for start in range(0, total, batch_size):
            batch = rows[start : start + batch_size]
            db.bulk_insert_mappings(SupportKB, batch)
            db.commit()
            print(f"inserted {min(start + batch_size, total)}/{total}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="data/raw/support_kb.csv", type=Path)
    parser.add_argument("--batch-size", default=500, type=int)
    args = parser.parse_args()

    df = load_and_clean(args.csv)
    load_into_db(df, args.batch_size)
    print("done: support_kb populated (embeddings are still null)")


if __name__ == "__main__":
    main()
