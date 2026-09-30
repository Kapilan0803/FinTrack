import os

# Default to development settings if DJANGO_SETTINGS_MODULE is not set
env_settings = os.getenv('DJANGO_ENV', 'development')
if env_settings == 'production':
    from .production import *
else:
    from .development import *
