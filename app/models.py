from enum import Enum
from typing import List
from sqlalchemy import Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.extensions import db
from decimal import Decimal
from flask_login import UserMixin

class TypeEnum(Enum):
  INCOME = "income"
  EXPENSE = "expense"

# Create Models
class User(db.Model, UserMixin):
  __tablename__ = "users"
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
  hash: Mapped[str] = mapped_column(String(255), nullable=False)
  
  # RELATIONSHIPS
  user_categories: Mapped[List["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")
  user_transactions: Mapped[List["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Category(db.Model):
  __tablename__ = "categories"
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
  name: Mapped[str] = mapped_column(String(50), nullable=False)
  type: Mapped[TypeEnum] = mapped_column(SQLEnum(TypeEnum), nullable=False)
  
  # RELATIONSHIPS
  user: Mapped["User"] = relationship(back_populates="user_categories")
  transactions: Mapped[List["Transaction"]] = relationship(back_populates="category")

class Transaction(db.Model):
  __tablename__ = "transactions"
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
  category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
  amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
  concept: Mapped[str] = mapped_column(String(100), nullable=False)
  type: Mapped[TypeEnum] = mapped_column(SQLEnum(TypeEnum), nullable=False)
  date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  
  # RELATIONSHIPS
  user: Mapped["User"] = relationship(back_populates="user_transactions")
  category: Mapped["Category"] = relationship(back_populates="transactions")