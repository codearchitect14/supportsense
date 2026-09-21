# Data

This folder is reproducible from scratch using the commands below. Nothing under
`data/raw`, `data/processed`, or `data/embeddings` is committed to source control;
only this README and the loading scripts in `data/scripts` are tracked.

## 1. Support knowledge base dataset

Source: Hugging Face, `bitext/Bitext-customer-support-llm-chatbot-training-dataset`
License: Community Data License Agreement - Sharing (CDLA-Sharing)

Download:

```bash
pip install datasets
python - <<'PY'
from datasets import load_dataset
ds = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset")
ds["train"].to_csv("data/raw/support_kb.csv", index=False)
PY
```

Load into PostgreSQL:

```bash
python data/scripts/load_support_kb.py
```

## 2. Revenue and operations dataset

Source: Kaggle, `olistbr/brazilian-ecommerce`
License: released by Olist for public research and demonstration use; see the
dataset page on Kaggle for the current terms.

Download:

```bash
pip install kaggle
# Place a Kaggle API token at ~/.kaggle/kaggle.json first (requires a free Kaggle account).
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/olist --unzip
```

Load into PostgreSQL:

```bash
python data/scripts/build_star_schema.py
```

## 3. Validate the loaded data

After both loaders have run:

```bash
python data/scripts/validate_data.py
```

This checks row counts, required-column null rates, and foreign key integrity
across the support knowledge base and the Olist star schema, and exits with a
non-zero status and a full list of failures if anything looks wrong.

## 4. Folder structure

```
data/
  raw/
    support_kb.csv
    olist/
      olist_orders_dataset.csv
      olist_order_items_dataset.csv
      olist_order_payments_dataset.csv
      olist_order_reviews_dataset.csv
      olist_customers_dataset.csv
      olist_products_dataset.csv
      olist_sellers_dataset.csv
  processed/
    support_kb_cleaned.parquet
    olist_star_schema/
  embeddings/
    support_kb_embeddings.parquet
  scripts/
    load_support_kb.py
    build_star_schema.py
    validate_data.py
    generate_embeddings.py   (added in Phase 5, with the embedding service)
```

## 5. Prerequisites

Before running the loaders, apply the database migrations from the backend so
the target tables exist:

```bash
cd backend
alembic upgrade head
```

`DATABASE_URL` must point at a PostgreSQL instance with the pgvector extension
available (the `docker-compose.yml` at the repository root provides this via
the `pgvector/pgvector` image).
