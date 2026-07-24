# Deployment and Alembic Migrations

This project uses Alembic for database schema changes. When a new server version depends on a migration, run the migration before starting the new server container.

## What the `20260716_align_history_with_irrigation_result` migration does

- Adds the new history columns needed by the extended `IrrigationResult` contract.
- Keeps the columns nullable so older history rows remain readable.
- Preserves backward compatibility with the existing SQLite database file.

## Safe production update flow

If you currently deploy with:

```bash
docker compose down
git stash
git pull
git stash pop
docker compose up --build
```

use this updated order instead:

```bash
docker compose down
git stash
git pull
git stash pop
docker compose build server
docker compose run --rm server alembic upgrade head
docker compose up -d --build
```

## Notes

- Run the migration exactly once per new schema revision.
- If the migration fails, do not start the new server container until the issue is fixed.
- Because the migration only adds nullable columns, older data stays valid and the previous server version can still read the database.
- For rollback, restore the database backup first; Alembic downgrade should be treated as a last resort.

## Recommended checklist

1. Back up `runtime/server/data/sis.db`.
2. Pull the new code.
3. Build the new `server` image.
4. Run `docker compose run --rm server alembic upgrade head`.
5. Start the stack with `docker compose up -d --build`.
