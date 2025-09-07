#!/bin/bash
echo "Starting Celery worker..."
celery -A app.celery worker --loglevel=info
