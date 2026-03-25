#!/bin/sh
set -eu

: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

DB_HOST="${DB_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_WAIT_TIMEOUT="${POSTGRES_WAIT_TIMEOUT:-60}"
POSTGRES_WAIT_INTERVAL="${POSTGRES_WAIT_INTERVAL:-1}"

export PGPASSWORD="$POSTGRES_PASSWORD"

elapsed=0
while ! pg_isready -h "$DB_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
  elapsed=$((elapsed + POSTGRES_WAIT_INTERVAL))
  if [ "$elapsed" -ge "$POSTGRES_WAIT_TIMEOUT" ]; then
    echo "Postgres is not ready after ${POSTGRES_WAIT_TIMEOUT}s"
    exit 1
  fi
  sleep "$POSTGRES_WAIT_INTERVAL"
done

echo "Postgres is ready"
