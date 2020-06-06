# -*- coding: utf-8 -*-
"""Application configuration."""
import datetime
import os


class Config(object):
    """Base configuration."""

    SECRET_KEY = os.environ.get('WOLFGANG_SECRET', 'secret-key')  # TODO: Change me
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    BCRYPT_LOG_ROUNDS = 13
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_FAKE_TOKEN = False
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=1)
    SWAGGER_UI_LANGUAGES = ['en']
    SWAGGER_VALIDATOR_URL = ''
    SWAGGER_UI_OAUTH_CLIENT_ID = None
    SWAGGER_UI_JSONEDITOR = True
    YACHT_IMG_FOLDER = PROJECT_ROOT + '/wolfgang/uploads/yacht_img'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    CONTRACT_CHARGE_DOLLAR = 50



class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql://wolfdb:3306/wolfgang'  # TODO: Change me
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    # MAIL_USERNAME = os.environ['EMAIL_USER']
    # MAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
    STRIPE_KEYS = {
      'secret_key': os.environ.get('SECRET_KEY', None),
      'publishable_key': os.environ.get('PUBLISHABLE_KEY', None)
    }



class DockerDevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://wolfgang_dev:wolfgang_dev_password@wolfdb:3306/wolfgang'
    DEBUG_TB_ENABLED = True
    JWT_FAKE_TOKEN = os.environ.get('WOLFGANG_FAKE_USER_TOKEN')
    # MAIL_USERNAME = os.environ['EMAIL_USER']
    # MAIL_PASSWORD = os.environ['EMAIL_PASSWORD']


class LocalDevConfig(Config):
    """Development configuration."""

    ENV = 'localdev'
    DEBUG = True
    DB_NAME = 'local_dev.db'
    DB_PATH = os.path.join(Config.PROJECT_ROOT, DB_NAME)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}'.format(DB_PATH)
    DEBUG_TB_ENABLED = True
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=2)
    JWT_FAKE_TOKEN = os.environ.get('WOLFGANG_FAKE_USER_TOKEN')
    MAIL_USERNAME = 'ada.von.umlaut@gmail.com'
    MAIL_PASSWORD = 'test#125|9&83'
    STRIPE_KEYS = {
      'secret_key': 'sk_test_Nqd2ts1Rl8EErUrigntFcWN3',
      'publishable_key': 'pk_test_IkQeLppEHwtTJxmbknDrBXdD'
    }


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DEBUG = True
    DB_NAME = 'test_dev.db'
    # DB_PATH = os.path.join(Config.PROJECT_ROOT, DB_NAME)
    SQLALCHEMY_DATABASE_URI = 'sqlite://' # in-memory DB
    PRESERVE_CONTEXT_ON_EXCEPTION = False  # prevents double error when assert fails
    # SQLALCHEMY_DATABASE_URI = 'sqlite://'
    BCRYPT_LOG_ROUNDS = 4  # For faster tests; needs at least 4 to avoid "ValueError: Invalid rounds"
    WTF_CSRF_ENABLED = False  # Allows form testing
