#!/bin/bash
set -e

echo "========================================="
echo "   SPRAWL ENTERPRISE TEST SUITE (MOCK)   "
echo "========================================="

echo "[1/5] Cleaning previous test environments..."
sprawl clean-test --testmode || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -d ".dummy_dna" ]; then
    echo "[*] Creating temporary .dummy_dna repository for the test..."
    cp -r "$SCRIPT_DIR/../demo/dummy_dna_template" .dummy_dna
    cd .dummy_dna && git init -q && git config user.email "test@example.com" && git config user.name "Test" && git add . && git commit -q -m "init" && cd ..
fi

echo "\n[2/5] Initializing Sprawl Hub (Test Mode)..."
sprawl init file://$(pwd)/.dummy_dna --testmode



echo "\n[3/5] Scaffolding Workspace..."
rm -rf test-project-alpha
sprawl create test-project-alpha --testmode

echo "\n[4/5] Crafting Custom DNA Schema..."
mkdir -p test-project-alpha/.agents
cat <<EOF > test-project-alpha/.agents/sprawl_manifest.yml
# test-project-alpha

## [rules]
- architecture.md
- security.md

## [skills]
- cloud_deployer
- python_scraper

## [atoms]

## [workflows]

EOF

echo "\n[5/5] Synchronizing DNA..."
cd test-project-alpha
sprawl sync --testmode

echo "\n[*] Verifying Universal Sandbox Provisioning..."
if [ ! -d ".agents/.venv" ]; then
  echo "ERROR: Universal .venv sandbox was not provisioned!"
  exit 1
fi
echo "[+] Sandbox verified."

cd ..



echo -e "\n========================================="
echo "   TEST SUITE EXECUTED SUCCESSFULLY!     "
echo "========================================="
