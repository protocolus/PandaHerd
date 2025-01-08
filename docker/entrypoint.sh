#!/bin/bash
set -e

# Run database migrations
poetry run alembic upgrade head

# Execute the main command
exec "$@"
