import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
  SECRET_KEY = os.environ.get("SECRET_KEY")
  
  if not SECRET_KEY:
    print("CRITICAL: SECRET_KEY not set!")

  SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "instance", "finance.db")
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  SESSION_PERMANENT = False