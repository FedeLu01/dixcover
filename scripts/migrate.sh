#!/usr/bin/env bash
set -euo pipefail

# migrate.sh — run Alembic migrations against the project's database.
# Usage: ./migrate.sh [alembic-args]

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$PROJECT_ROOT":${PYTHONPATH:-}

# Ensure we run from the project root so alembic finds `alembic.ini` and `alembic/`.
cd "$PROJECT_ROOT"

echo "Running Alembic migrations (alembic upgrade head)"

# Allow passing through arguments to alembic (e.g. 'revision --autogenerate -m "msg"')
if [ "$#" -eq 0 ]; then
  alembic upgrade head
else
  alembic "$@"
fi

echo "Done."
