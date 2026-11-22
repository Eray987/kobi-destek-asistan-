"""Checks that the database is running and pgvector is installed.

Usage:  python scripts/check_db.py
"""

from kobi_asistan.db import connect, pgvector_version


def main() -> None:
    with connect() as conn:
        version = pgvector_version(conn)
        # Cosine distance between two vectors: 0 = same direction
        distance = conn.execute("SELECT '[1,0,0]'::vector <=> '[1,0,0]'::vector").fetchone()[0]
    print(f"Connected. pgvector version: {version}")
    print(f"Sample cosine distance (identical vectors): {distance}")


if __name__ == "__main__":
    main()
