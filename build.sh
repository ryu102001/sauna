#!/usr/bin/env bash
set -e

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Install Python requirements
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
SKIP_PREFLIGHT_CHECK=true ESLINT_NO_DEV_ERRORS=true CI=false REACT_APP_API_URL=${RENDER_EXTERNAL_URL} npm run build
cd ..

# Debug message
echo "Build completed successfully"
