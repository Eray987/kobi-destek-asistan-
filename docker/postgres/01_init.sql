-- Runs once, when the database is first created.
-- pgvector lets us store embedding vectors and run similarity search.
CREATE EXTENSION IF NOT EXISTS vector;
