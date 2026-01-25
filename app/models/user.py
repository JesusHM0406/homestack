from app.extensions import db
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
  from app.models.category import Category
  from app.models.transaction import Transaction

class User(db.Model, UserMixin):
  __tablename__ = "users"
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
  hash: Mapped[str] = mapped_column(String(255), nullable=False)
  
  # RELATIONSHIPS
  user_categories: Mapped[List["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")
  user_transactions: Mapped[List["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")