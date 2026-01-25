from app.extensions import db
from app.models.type_enum import TypeEnum
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from decimal import Decimal
from datetime import datetime

if TYPE_CHECKING:
  from app.models.user import User
  from app.models.category import Category

class Transaction(db.Model):
  __tablename__ = "transactions"
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
  category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
  amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
  concept: Mapped[str] = mapped_column(String(100), nullable=False)
  type: Mapped[TypeEnum] = mapped_column(SQLEnum(TypeEnum), nullable=False)
  date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=db.func.now(), nullable=False)
  
  # RELATIONSHIPS
  user: Mapped["User"] = relationship(back_populates="user_transactions")
  category: Mapped["Category"] = relationship(back_populates="transactions")