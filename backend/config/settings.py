import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # the backend/ folder

# Load backend/.env if present. The path is explicit (not CWD-relative) so it
# behaves identically under `runserver`, `manage.py`, and the PythonAnywhere
# WSGI worker, whose working directory is not the project folder.
# Values already present in the real environment win over the file.
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:  # pragma: no cover - dotenv is optional
    pass


def env_bool(name, default=False):
    """Read a boolean env var. Accepts 1/true/yes/on (case-insensitive)."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    """Read a comma-separated env var into a clean list."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-jakeala-naturals-change-in-production")
DEBUG = env_bool("DJANGO_DEBUG", True)

# Localhost stays allowed so `runserver` keeps working. Add live hosts with the
# ALLOWED_HOSTS env var, e.g. "jakeala.pythonanywhere.com,api.jakeala.com".
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")

# Refuse to boot in production with the placeholder key instead of silently
# running an insecure site.
if not DEBUG and SECRET_KEY == "dev-jakeala-naturals-change-in-production":
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set to a unique value when DJANGO_DEBUG=0. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_filters",
    "catalog",
    "commerce",
    "content",
    "accounts",
    "admin_api",
    "payments",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Log in with either the email address or the username.
AUTHENTICATION_BACKENDS = ["accounts.backends.EmailOrUsernameBackend"]

# Django's standard strength checks. Previously empty, which meant a one
# character password was accepted on registration.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS / CSRF
# ---------------------------------------------------------------------------
# Development allows every origin so `localhost:<any port>` just works.
# In production set CORS_ALLOWED_ORIGINS to the real front-end origins, e.g.
#   CORS_ALLOWED_ORIGINS=https://jakeala.com,https://www.jakeala.com
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
# Regexes for origins too dynamic to list one by one - Vercel gives every preview
# deployment its own hostname, so a whitelist alone would block those. Example:
#   CORS_ALLOWED_ORIGIN_REGEXES=^https://jakeala-naturals[a-z0-9-]*\.vercel\.app$
CORS_ALLOWED_ORIGIN_REGEXES = env_list("CORS_ALLOWED_ORIGIN_REGEXES")
CORS_ALLOW_ALL_ORIGINS = DEBUG and not (CORS_ALLOWED_ORIGINS or CORS_ALLOWED_ORIGIN_REGEXES)
CORS_ALLOW_CREDENTIALS = True

# Required by Django 4+ for POSTs (e.g. the Django admin login) behind a proxy.
# Use full scheme://host entries, e.g. https://jakeala.pythonanywhere.com
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000" if DEBUG else "",
)

# Throttling counters live in a file-based cache so limits survive web-app
# reloads (the default LocMemCache is wiped every time the worker restarts,
# which would hand an attacker a fresh allowance). The folder is gitignored.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / "cache",
        "TIMEOUT": 300,
        "OPTIONS": {"MAX_ENTRIES": 2000},
    }
}

# ---------------------------------------------------------------------------
# Production security
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "same-origin"
    # Stops other sites from getting a handle on our windows (tabnabbing).
    SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
    # PythonAnywhere terminates TLS at its proxy and forwards the scheme to us.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
    CSRF_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", True)
    SESSION_COOKIE_HTTPONLY = True
    # Remember HTTPS in the browser for a year. Off by default because a wrong
    # setting is painful to undo; enable once the domain is settled.
    if env_bool("DJANGO_HSTS", False):
        SECURE_HSTS_SECONDS = 31536000
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True
    if env_bool("DJANGO_SECURE_SSL_REDIRECT", False):
        SECURE_SSL_REDIRECT = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        # Rejects tokens older than AUTH_TOKEN_TTL (see below).
        "accounts.authentication.ExpiringTokenAuthentication",
    ],
    # Safer default: anything not explicitly marked AllowAny can only be read.
    # Every write endpoint now states its intent instead of inheriting "open".
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "PAGE_SIZE": 24,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        # Picks up a view's ``throttle_scope`` (or the scope baked into a class in
        # config/throttles.py) so each sensitive endpoint has its own budget.
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "240/min",
        "user": "1000/hour",
        # Credential endpoints: login, register, verification attempts.
        "auth": "12/min",
        # Outbound EmailJS messages. Free plan allows 200/month, so this is both
        # an abuse guard and a bill guard. Keyed per address and per caller.
        "email": "4/hour",
        "email_ip": "10/hour",
        "checkout": "30/hour",
        "contact": "6/hour",
        "newsletter": "6/hour",
        "admin_login": "10/min",
    },
}

# Most a single line may hold, so a typo (or a script) cannot fill the database.
CART_MAX_QUANTITY = int(os.environ.get("CART_MAX_QUANTITY", "99"))

# ---------------------------------------------------------------------------
# Test-only shortcuts
# ---------------------------------------------------------------------------
# `manage.py test` creates users and verification codes by the hundred, and
# PBKDF2 hashing makes that take minutes. These overrides apply *only* while tests
# run, and never to a real deployment:
#   * a fast hasher, so the suite runs in seconds;
#   * an in-memory cache, so throttle counters do not leak between tests and no
#     files are written to backend/cache/.
if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "jakeala-tests",
        }
    }
    # Keep the suite fast even if email is configured on the developer's machine.
    EMAILJS_SERVICE_ID = ""
    EMAILJS_PUBLIC_KEY = ""
    EMAILJS_PRIVATE_KEY = ""



# How long an API token stays valid. Tokens used to live forever; now a stolen
# one stops working. Signing in again issues a fresh one.
AUTH_TOKEN_TTL = int(os.environ.get("AUTH_TOKEN_TTL_DAYS", "30")) * 86400

# Public URL of the API itself, used to build links inside emails.
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
# Where the front end lives, used in email links (verify / reset password).
SITE_URL = os.environ.get("SITE_URL", "http://localhost:3000")

# ---------------------------------------------------------------------------
# Transactional email - EmailJS (https://emailjs.com)
# ---------------------------------------------------------------------------
# PythonAnywhere's free plan blocks outbound SMTP, so mail is sent over HTTP.
# Create a service + template, then paste the four values below into backend/.env.
# EMAILJS_PRIVATE_KEY authorises *server-side* sends - it must never reach the
# browser (that is why the codes are generated here, not in the front end).
EMAILJS_SERVICE_ID = os.environ.get("EMAILJS_SERVICE_ID", "")
EMAILJS_PUBLIC_KEY = os.environ.get("EMAILJS_PUBLIC_KEY", "")
EMAILJS_PRIVATE_KEY = os.environ.get("EMAILJS_PRIVATE_KEY", "")
EMAILJS_TEMPLATE_VERIFY = os.environ.get("EMAILJS_TEMPLATE_VERIFY", "")
EMAILJS_TEMPLATE_RESET = os.environ.get("EMAILJS_TEMPLATE_RESET", "")
EMAILJS_TEMPLATE_ORDER = os.environ.get("EMAILJS_TEMPLATE_ORDER", "")
EMAILJS_TIMEOUT = int(os.environ.get("EMAILJS_TIMEOUT", "12"))

# With no keys configured we log the code to the console instead of sending it,
# so registration can be tested locally before EmailJS is wired up.
EMAIL_ENABLED = bool(
    EMAILJS_SERVICE_ID and EMAILJS_PUBLIC_KEY and EMAILJS_PRIVATE_KEY and EMAILJS_TEMPLATE_VERIFY
)

# How long a 6-digit verification code stays valid, and how many wrong guesses
# before it is burned. Guessing is also rate-limited.
VERIFICATION_CODE_TTL_MINUTES = int(os.environ.get("VERIFICATION_CODE_TTL_MINUTES", "15"))
VERIFICATION_MAX_ATTEMPTS = int(os.environ.get("VERIFICATION_MAX_ATTEMPTS", "5"))

# ---------------------------------------------------------------------------
# Payments - Paystack (https://paystack.com)
# ---------------------------------------------------------------------------
# Test keys work end to end with the test cards; swap in live keys to go live.
#   sk_test_xxx / pk_test_xxx  -> sandbox
#   sk_live_xxx / pk_live_xxx  -> real money
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_CURRENCY = os.environ.get("PAYSTACK_CURRENCY", "NGN")
# Where Paystack sends the shopper after payment; the front end verifies there.
PAYSTACK_CALLBACK_URL = os.environ.get(
    "PAYSTACK_CALLBACK_URL", f"{SITE_URL}/payment/verify"
)
PAYSTACK_TIMEOUT = int(os.environ.get("PAYSTACK_TIMEOUT", "20"))
# Free shipping threshold, in naira.
FREE_SHIPPING_THRESHOLD = int(os.environ.get("FREE_SHIPPING_THRESHOLD", "15000"))
FLAT_SHIPPING_FEE = int(os.environ.get("FLAT_SHIPPING_FEE", "2500"))

