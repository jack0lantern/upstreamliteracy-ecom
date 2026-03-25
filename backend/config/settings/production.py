import os

from .base import *  # noqa: F401, F403

DEBUG = False
# Railway health checks hit the container over HTTP; TLS is still terminated at the edge.
_on_railway = bool(os.environ.get("RAILWAY_ENVIRONMENT"))
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not _on_railway)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
