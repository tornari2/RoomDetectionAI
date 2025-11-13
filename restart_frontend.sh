#!/bin/bash
# Restart the frontend dev server to pick up the .env configuration

echo "Stopping any running frontend dev servers..."
pkill -f "node.*frontend.*vite" || true

echo "Waiting for processes to stop..."
sleep 2

cd /Users/michaeltornaritis/Desktop/WK4_RoomDetectionAI/frontend

echo "Starting frontend dev server..."
echo "API URL: $(cat .env | grep VITE_API_BASE_URL)"
echo ""

npm run dev

