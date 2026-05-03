#!/bin/sh
# Entry point script for K-Line backend container
# Ensures database is initialized before starting the app
set -e

echo "[entrypoint] Starting K-Line Backend..."

# Initialize database (tables created by PostgresStorage/SQLiteStorage)
python -c "
from backend.app.dependencies import get_storage
storage = get_storage()
print('[entrypoint] Database initialized successfully')
"

# Initialize project directories and configurations
python scripts/setup.py || echo "[entrypoint] setup.py completed with warnings"

# Execute the main command
echo "[entrypoint] Starting uvicorn..."
exec "$@"
