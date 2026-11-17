# Schema Migrations

Numbered Cypher migration files for all schema changes.

## Rules
1. Number sequentially: `001_initial.cypher`, `002_add_x.cypher`
2. Use `MERGE` and `IF NOT EXISTS` — migrations are idempotent
3. Never modify after running on production
4. New node labels or edge types require a GitHub issue and Rey approval first
