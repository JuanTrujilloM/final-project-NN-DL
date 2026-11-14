#!/bin/sh
set -e
python download_weights.py
exec python -m uvicorn app.backend.main:app --host 0.0.0.0 --port 7860
