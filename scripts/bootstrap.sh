#!/usr/bin/env bash
# Bootstrap a development environment for hydradb-cli.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

# ── Python check ─────────────────────────────────────────────────────────────
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[!] Python 3.10+ is required but not found."
    exit 1
fi

version=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

# Verify the detected Python is actually 3.10+
if ! $PYTHON -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "[!] Python ${version} detected but 3.10+ is required."
    exit 1
fi

echo "[ok] Python ${version} detected"

# ── Virtual environment ──────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "[ok] Creating virtual environment at ${VENV_DIR}"
    $PYTHON -m venv "$VENV_DIR"
else
    echo "[ok] Virtual environment already exists at ${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
echo "[ok] Activated virtual environment"

# ── Install ──────────────────────────────────────────────────────────────────
pip install --quiet --upgrade pip
echo "[ok] pip upgraded"

pip install --quiet -e "${REPO_ROOT}[dev]"
echo "[ok] Installed package in editable mode (with dev tools)"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "[ok] Bootstrap complete! Next steps:"
echo "  1. Activate the venv:  source .venv/bin/activate"
echo "  2. Run the CLI:        hydradb --help"
echo "  3. Run tests:          make test"
echo ""
echo "  Run 'make help' to see all available targets."
