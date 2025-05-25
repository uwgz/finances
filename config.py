from decouple import config
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = config("SECRET_KEY", default="hard to guess string")
    MAIL_SERVER = config("MAIL_SERVER", default="smtp.googlemail.com")
    MAIL_PORT = config("MAIL_PORT", default=587, cast=int)
    MAIL_USE_TLS = config("MAIL_USE_TLS", default=True, cast=bool)
    MAIL_USERNAME = config("MAIL_USERNAME", default=None)
    MAIL_PASSWORD = config("MAIL_PASSWORD", default=None)
    FLASKY_MAIL_SUBJECT_PREFIX = "[Flasky]"
    FLASKY_MAIL_SENDER = "Flasky Admin <flasky@example.com>"
    FLASKY_ADMIN = config("FLASKY_ADMIN", default=None)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = config(
        "DEV_DATABASE_URL",
        default="sqlite:///" + os.path.join(basedir, "data-dev.sqlite"),
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = config("TEST_DATABASE_URL", default="sqlite://")


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = config(
        "DATABASE_URL", default="sqlite:///" + os.path.join(basedir, "data.sqlite")
    )


config_dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}