# =============================================================================
#  PythonAnywhere WSGI configuration  —  Jakeala Naturals backend
# -----------------------------------------------------------------------------
#  HOW TO USE
#    1. Web tab -> "Add a new web app" -> "Manual configuration" -> Python 3.10
#       (the same version you used for the virtualenv).
#    2. Fill in the "Virtualenv" box:  /home/<your-username>/.virtualenvs/jakeala-venv
#    3. Click the "WSGI configuration file" link (a path like
#       /var/www/<your-username>_pythonanywhere_com_wsgi.py), select everything,
#       delete it, then paste everything below this comment block.
#    4. Make sure /home/<your-username>/Jakeala_Naturals/backend/.env exists
#       (copy it from .env.example) BEFORE reloading.
#    5. Save, then hit "Reload" in the Web tab.
#
#  THERE IS NOTHING TO EDIT IN THIS FILE. The home directory is resolved at
#  runtime, so your username never has to be typed in. All DJANGO_* settings are
#  read from backend/.env by config/settings.py, which keeps the web worker and
#  your Bash consoles on one source of truth.
# =============================================================================

import os
import sys

# ---- 1. Project path: the folder that contains manage.py --------------------
# os.path.expanduser("~") resolves to /home/<your-username> on PythonAnywhere,
# so this works on any account as-is.
PROJECT_DIR = os.path.join(os.path.expanduser("~"), "Jakeala_Naturals", "backend")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# ---- 2. Django settings module ---------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# ---- 3. (Optional) overrides -----------------------------------------------
# Anything set here takes precedence over backend/.env. Uncomment if you would
# rather keep secrets out of the filesystem entirely.
#
# os.environ["DJANGO_DEBUG"] = "0"
# os.environ["DJANGO_SECRET_KEY"] = "paste-a-long-random-string"
# os.environ["ALLOWED_HOSTS"] = "yourname.pythonanywhere.com"

# ---- 4. Django WSGI application --------------------------------------------
from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
