#!/bin/bash

set -e

PROJECT_NAME="Bible-RAG"
OUTPUT_ZIP="${PROJECT_NAME}_light.zip"

echo "Creating ${OUTPUT_ZIP}..."

rm -f "$OUTPUT_ZIP"

zip -r "$OUTPUT_ZIP" . \
  -x "data/*" \
  -x "frontend/node_modules/*" \
  -x ".git/*" \
  -x ".idea/*" \
  -x ".vscode/*" \
  -x "__pycache__/*" \
  -x "*/__pycache__/*" \
  -x "*.pyc" \
  -x ".DS_Store" \
  -x "*/.DS_Store" \
  -x ".env" \
  -x "backend/.env" \
  -x "frontend/.env" \
  -x "frontend/.env.local" \
  -x "*.log" \
  -x "eval/results/*" \
  -x "frontend/dist/*" \
  -x "build/*" \
  -x "dist/*" \
  -x "*.zip"

echo "Done: ${OUTPUT_ZIP}"
