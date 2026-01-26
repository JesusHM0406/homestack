import os

class Config:
  SECRET_KEY = os.getenv("SECRET_KEY")
  SESSION_PERMANENT = False
  SQLALCHEMY_DATABASE_URI = "sqlite:///finance.db"
  SQLALCHEMY_TRACK_MODIFICATIONS = False