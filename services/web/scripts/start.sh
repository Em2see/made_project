#!/bin/bash
echo Starting Flask example app.
cd /app
gunicorn -w 2 -b 0.0.0.0:8080 app:app
