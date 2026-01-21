import os

from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from models import User, Category, Transaction
from extensions import db
from sqlalchemy import func

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

with app.app_context():
  db.create_all()

@app.route("/")
@login_required
def index():
  user_id = session.get("user_id")
  
  user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one_or_none()
  
  if not user:
    flash("Ocurrio un error, por favor intenta iniciar sesión de nuevo")
    return redirect(url_for("login"))
  
  # Get Balance
  
  balance_stmt = (
    db.select(
      func.sum(
        db.case((Category.type == "income", Transaction.amount), else_=0)
      ) -
      func.sum(
        db.case((Category.type == "expense", Transaction.amount), else_=0)
      )
    )
    .join(Category)
    .where(Transaction.user_id == user_id)
  )

  balance = db.session.execute(balance_stmt).scalar() or 0
  
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