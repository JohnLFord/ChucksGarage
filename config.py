import os

from dotenv import load_dotenv

load_dotenv()


class DevelopmentConfig:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]