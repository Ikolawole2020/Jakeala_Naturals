#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Deploy / update the Jakeala Naturals backend on PythonAnywhere.
#
# Run this in a PythonAnywhere Bash console:
#     cd ~/Jakeala_Naturals/backend && bash deploy.sh
#
# Then hit "Reload" on the Web tab (the last step opens that page for you).
# ---------------------------------------------------------------------------
set -euo pipefail

REPO_DIR="$HOME/Jakeala_Naturals"
BACKEND_DIR="$REPO_DIR/backend"
VENV="$HOME/.virtualenvs/jakeala-venv"

echo "==> Pulling latest code from GitHub"
cd "$REPO_DIR"
git pull --ff-only

echo "==> Activating virtualenv: $VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

echo "==> Installing requirements"
pip install --quiet --upgrade -r "$BACKEND_DIR/requirements.txt"

cd "$BACKEND_DIR"

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Running Django system checks"
python manage.py check

echo
echo "Done. Now click Reload at: https://www.pythonanywhere.com/web_app_setup/"
echo "(If this is the very first deploy, also run: python manage.py seed)"
