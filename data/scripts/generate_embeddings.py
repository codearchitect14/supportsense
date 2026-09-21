"""Embeds every support_kb row that doesn't have an embedding yet and stores
the vectors via pgvector.

Usage:
    python data/scripts/generate_embeddings.py [--batch-size 64] [--all]

--all re-embeds every row (use after changing EMBEDDING_MODEL).
"""
import argparse

import _pathsetup  # noqa: F401  (adds backend/ to sys.path)

from app.db.session import SessionLocal
from app.models.support_kb import SupportKB
from app.services.embedding_service import get_embedding_service


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", default=64, type=int)
    parser.add_argument("--all", action="store_true", help="re-embed every row, not just missing ones")
    args = parser.parse_args()

    embedding_service = get_embedding_service()
    db = SessionLocal()
    try:
        query = db.query(SupportKB)
        if not args.all:
            query = query.filter(SupportKB.embedding.is_(None))
        rows = query.all()

        total = len(rows)
        print(f"embedding {total} row(s)")
        for start in range(0, total, args.batch_size):
            batch = rows[start : start + args.batch_size]
            # Embed the customer-phrased instruction, not the agent-phrased
            # response: incoming queries are also customer-phrased
            # questions, so question-to-question matching is far more
            # accurate than question-to-answer matching, and the response
            # is what gets returned once its instruction matches.
            vectors = embedding_service.embed_passages([row.instruction for row in batch])
            for row, vector in zip(batch, vectors):
                row.embedding = vector
            db.commit()
            print(f"embedded {min(start + args.batch_size, total)}/{total}")
    finally:
        db.close()

    print("done: support_kb embeddings populated")


if __name__ == "__main__":
    main()
