#!/bin/bash
# Mantle Intel Agent — Quick Setup Script
set -e

echo "═══════════════════════════════════════════"
echo "  Mantle Intel Agent — Setup"
echo "═══════════════════════════════════════════"

# Python deps
echo "→ Installing Python dependencies..."
pip install -r requirements.txt

# Contract deps
echo "→ Installing contract dependencies..."
cd contracts && npm install && cd ..

# Dashboard deps
echo "→ Installing dashboard dependencies..."
cd dashboard && npm install && cd ..

# Create data dir
mkdir -p data

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. cp .env.example .env && edit .env"
echo "  2. python main.py --cycles 3           # test demo"
echo "  3. cd contracts && npx hardhat run scripts/deploy.js --network mantle_testnet"
echo "  4. cd dashboard && npm run build && cd .."
echo "  5. uvicorn server:app --host 0.0.0.0 --port 8000"
