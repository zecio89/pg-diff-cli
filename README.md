# pg-diff-cli

> Command-line utility to diff two PostgreSQL schemas and output migration SQL.

---

## Installation

```bash
pip install pg-diff-cli
```

Or install from source:

```bash
git clone https://github.com/yourname/pg-diff-cli.git
cd pg-diff-cli
pip install .
```

---

## Usage

Compare two PostgreSQL databases and print the migration SQL to stdout:

```bash
pg-diff \
  --source "postgresql://user:pass@localhost:5432/db_old" \
  --target "postgresql://user:pass@localhost:5432/db_new"
```

Save the output to a file:

```bash
pg-diff \
  --source "postgresql://user:pass@localhost/db_old" \
  --target "postgresql://user:pass@localhost/db_new" \
  --output migration.sql
```

### Options

| Flag | Description |
|------|-------------|
| `--source` | Connection string for the source (baseline) database |
| `--target` | Connection string for the target (desired) database |
| `--output` | Write SQL to a file instead of stdout |
| `--schema` | Limit diff to a specific schema (default: `public`) |
| `--dry-run` | Print the diff without writing any output |

### Example Output

```sql
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
CREATE INDEX idx_orders_user_id ON orders (user_id);
DROP TABLE legacy_sessions;
```

---

## Requirements

- Python 3.8+
- PostgreSQL 12+

---

## License

[MIT](LICENSE)