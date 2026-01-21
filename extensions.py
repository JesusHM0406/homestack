from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Initialize extension
class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)