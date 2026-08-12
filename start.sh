#!/bin/sh
set -e
PORT="${PORT:-5001}"
exec gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --timeout 180 --preload app:app
