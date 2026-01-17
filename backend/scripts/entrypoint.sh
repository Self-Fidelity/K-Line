#!/bin/sh
# Entry point script for backend container
# Ensure database is initialized before starting the app

# Run DB initialization script (creates tables if they do not exist)
python backend/scripts/init_db.py
python scripts/setup.py

# Execute the original command (uvicorn)
exec "$@"
