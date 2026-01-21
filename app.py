import os

from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from enum import Enum
from typing import List
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

# Initialize extension
class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

# Initialize flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Session config
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
# Init session
Session(app)

db.init_app(app)

class TypeEnum(Enum):
  INCOME = "income"
  EXPENSE = "expense"

# Create Models
class User(db.Model):
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
  category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
  amount: Mapped[float] = mapped_column(Float, nullable=False)
  concept: Mapped[str] = mapped_column(String(100), nullable=False)
  date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  
  # RELATIONSHIPS
  user: Mapped["User"] = relationship(back_populates="user_transactions")
  category: Mapped["Category"] = relationship(back_populates="transactions")

with app.app_context():
  db.create_all()

@app.route("/")
@login_required
def index():
  return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
  
  if request.method == "POST":
    MIN_PASSWORD_SIZE = 8
    
    username = request.form.get("username")
    password = request.form.get("password")
    confirm = request.form.get("confirm")

    # Verify that the user input is not blank
    if not username or not password or not confirm:
      flash("Todos los datos son obligatorios", category="danger")
      return redirect(url_for("register"))

    # We need to check if that username already exists in our database since it stores unique usernames
    user_exists = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

    if user_exists:
      flash("Ya existe ese nombre de usuario, intenta con otro", category="danger")
      return redirect(url_for("register"))

    # We need to validate if that password contains a minimun of 8 characters for security
    if len(password) < MIN_PASSWORD_SIZE:
      flash(f"La contraseña debe contener un minimo de {MIN_PASSWORD_SIZE} caracteres", category="danger")
      return redirect(url_for("register"))

    # If the username is correct (unique) and the password is valid, then we need to compare the password with the confirmation
    if password != confirm:
      flash("Las contraseñas no coinciden", category="danger")
      return redirect(url_for("register"))

    # If all the data is correct, then now we can insert the user in the database
    try:
      # First we need to make the hash of the password
      password_hash = generate_password_hash(password)

      # Then we insert the user in the database
      new_user = User(username=username, hash=password_hash)
      db.session.add(new_user)
      db.session.commit()

      # The registration was successful
      flash("¡Registro exisotso! Ya puedes iniciar sesión", category="success")

      # Redirect user to login page
      return redirect(url_for("login"))
    except Exception as e:
      db.session.rollback()
      flash("Ocurrio un error al registrar el usuario. Intentalo de nuevo", category="danger")
      return redirect(url_for("register"))
  
  return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
  # Clear all sessions before log in
  session.clear()

  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    # User inputs are blank
    if not username or not password:
      flash("Debe proporcionar usuario y contraseña", category="danger")
      return render_template("login.html")

    """
    Replace this with the ORM migration
    """

    user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

    # There is no user with that username or the password is incorrect
    if not user or not check_password_hash(user.hash, password):
      flash("Nombre de usuario y/o contraseña invalidos", category="danger")
      return render_template("login.html")

    # Login user
    session["user_id"] = user.id
    session["username"] = user.username

    return redirect("/")
  
  return render_template("login.html")

@app.route("/logout")
def logout():
  session.clear()
  
  return redirect(url_for("login"))