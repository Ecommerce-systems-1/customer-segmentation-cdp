# Data Model — Customer Segmentation CDP

```sql
CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, total_orders INTEGER DEFAULT 0, total_spent REAL DEFAULT 0, last_order_date TEXT, segment TEXT DEFAULT 'unknown', created_at TEXT DEFAULT (datetime('now')));
```
