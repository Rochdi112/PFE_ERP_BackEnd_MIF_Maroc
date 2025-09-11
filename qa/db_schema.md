# DB Schema & Migrations

## Migrations Test

- Upgrade head: Not run (DB not running)
- Downgrade -1: Not run (DB not running)
- Upgrade head: Not run (DB not running)

## Schema Inspection

Command: python inspect_db.py

Output: DB not running (host "db" not found)

## Controls

- PK/FK/UNIQUE/CHECK: To be verified from SQLAlchemy models
- Index on FK: To be verified
- Zero-downtime strategy: Assumed implemented

## Criteria

- Migrations reversible: To be verified
- Integrity référentielle OK: To be verified

## Artifacts

- qa/db_indexes.sql: To be generated from DB
