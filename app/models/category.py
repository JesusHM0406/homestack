from app.extensions import db
from sqlalchemy import Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from app.models.type_enum import TypeEnum

if TYPE_CHECKING:
  from app.models.user import User
  from app.models.transaction import Transaction

class Category(db.Model):
  __tablename__ = "categories"
  
  id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
  name: Mapped[str] = mapped_column(String(50), nullable=False)
  type: Mapped[TypeEnum] = mapped_column(SQLEnum(TypeEnum), nullable=False)
  
  # RELATIONSHIPS
  user: Mapped["User"] = relationship(back_populates="user_categories")
  transactions: Mapped[List["Transaction"]] = relationship(back_populates="category")