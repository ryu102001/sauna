#!/usr/bin/env bash

# Build frontend
cd frontend
npm install
CI=false npm run build
cd ..

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Install Python requirements
pip install -r requirements.txt
