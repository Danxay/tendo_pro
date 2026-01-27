# Bolt's Journal

## 2026-01-27 - Missing Foreign Key Indexes in SQLite
**Learning:** SQLite does not automatically create indexes for foreign keys. This caused N+1-like performance issues when filtering by foreign keys (e.g., finding orders for a specific executor or customer).
**Action:** Always verify if FK columns need explicit indexes in SQLite, especially for columns used in `WHERE` or `JOIN` clauses.
