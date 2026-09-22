# =============================================================================
#  PythonAnywhere WSGI configuration  —  Jakeala Naturals backend
# -----------------------------------------------------------------------------
#  HOW TO USE
#    1. Web tab -> "Add a new web app" -> "Manual configuration" -> pick the
#       same Python version you used for the virtualenv (e.g. Python 3.10).
#    2. Set "Virtualenv" to:   /home/<USER>/.virtualenvs/jakeala-venv
#    3. Click the "WSGI configuration file" link (a path like
#       /var/www/<USER>_pythonanywhere_com_wsgi.py), select everything, delete
#       it, and paste the block below.
#    4. Replace every <USER> with your PythonAnywhere username.
#    5. Make sure /home/<USER>/Jakeala_Naturals/backend/.env exists (copy it
#       from .env.production.example) BEFORE reloading.
#    6. Hit "Reload" in the Web tab.
#
#  Note: the DJANGO_* settings are read from backend/.env by config/settings.py,
#  so that the web worker and your Bash consoles share one source of truth.
# =============================================================================

import os
import sys

# ---- 1. Project path: the folder that contains manage.py --------------------
PROJECT_DIR = "/home/<USER>/Jakeala_Naturals/backend"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# ---- 2. Django settings module --------------------------------------------
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

# ---- 3. (Optional) override the .env from here ----------------------------
#  Anything set here takes precedence over backend/.env, which is handy if you
#  would rather keep secrets out of the filesystem. Uncomment as needed:
#
# os.environ["DJANGO_DEBUG"] = "0"
# os.environ["DJANGO_SECRET_KEY"] = "paste-a-long-random-string"
# os.environ["ALLOWED_HOSTS"] = "<USER>.pythonanywhere.com"

# ---- 4. Django WSGI application -------------------------------------------
from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
