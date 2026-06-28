#!/bin/bash
set -e
cd "$(dirname "$0")/../frontend"
npm ci
npm run build
rm -rf ../backend/static
cp -r dist ../backend/static
echo "Frontend built to ../backend/static/"
