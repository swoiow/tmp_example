from .settings import *


SECRET_KEY = os.urandom(32)

DEBUG = False

ALLOWED_HOSTS = ["*"]
SESSION_COOKIE_DOMAIN = os.environ["MAIN_DOMAIN"]
SESSION_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
