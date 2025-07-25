"""
Django settings for ebilling_project project.

Generated by 'django-admin startproject' using Django 5.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-iief5x7_0$a1x2$b1p!xpukmt9z(zposqthk&rw*-06kx6#1_8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["exeesa.com", 'localhost', '127.0.0.1', 'www.exeesa.com', ".exeesa.com"]


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'billing',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ebilling.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                 'billing.context_processors.expiring_soon_products',
            ],
        },
    },
]

WSGI_APPLICATION = 'ebilling.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ebilling',
        'USER': 'postgres',
        'PASSWORD': 'Solution@97',
        'HOST': '217.145.69.172',
        'PORT': '5432',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

CORS_ALLOW_ALL_ORIGINS = True

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# settings.py
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
        },
        '404_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/404.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', '404_file'],  # Both handlers here
            'level': 'WARNING',  # Handles WARNING and above (including ERROR)
            'propagate': False,
        },
        'django.security.DisallowedHost': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
JAZZMIN_SETTINGS = {
    # Branding
    "site_title": "Exeesa",
    "site_header": "Exeesa",
    "site_brand": "Exeesa App",
    "site_logo": "logo/Capture.PNG",
    "login_logo": "logo/Capture4.png",
    "site_logo_classes": "img-circle",
    "welcome_sign": "Welcome to Exeesa Admin ",
    "copyright": "Exeesa Team",
    # User menu
    

    # Sidebar and navigation
    "show_sidebar": True,
    "navigation_expanded": True,
    # "order_with_respect_to": ["auth", "books", "books.author", "books.book"],

    # Custom links (for quick access actions)
    "custom_links": {
        "books": [{
            "name": "Make Messages",
            "url": "make_messages",
            "icon": "fas fa-comments",
            "permissions": ["books.view_book"]
        }]
    },

    # Icons (Font Awesome 5)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "billing.Branch": "fas fa-code-branch",          # Branch icon
        "billing.Party": "fas fa-user-friends",          # Party (customer/supplier)
        "billing.Product": "fas fa-box-open",            # Products
        "billing.Invoice": "fas fa-file-invoice-dollar", # Invoices
        "billing.InvoiceItem": "fas fa-list-ul",         # Invoice Items
        "billing.Payment": "fas fa-credit-card",  
        "billing.TotalBalance": "fas fa-wallet",  # 🪙 For TotalBalance
       "billing.Sales_invoice_settings": "fas fa-cogs"
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # Change view format
    "changeform_format": "horizontal_tabs",
   
   
 
}
