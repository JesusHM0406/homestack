import os

from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Session config
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize database
db = SQL("sqlite:///database.db")

@app.route("/")
def index():
  return "Hello"

@app.route("/register", methods=["GET", "POST"])
def register():
  
  # The user reached the page via the navigation bar or via link
  if request.method == "GET":
    return render_template("register.html")
  
  MIN_PASSWORD_SIZE = 8
  
  # The user submited his info
  username = request.form.get("username")
  password = request.form.get("password")
  confirm = request.form.get("confirm")
  
  # Verify that the user input is not blank
  if not username or not password or not confirm:
    flash("Todos los datos son obligatorios", category="danger")
    return redirect(url_for("register"))
  
  # We need to check if that username already exists in our database since it stores unique usernames
  user_exists = db.execute("SELECT * FROM users WHERE username = ?", username)
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
    db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, password_hash)
    
    # The registration was successful
    flash("¡Registro exisotso! Ya puedes iniciar sesión.", category="success")
    
    # Redirect user to login page
    return redirect(url_for("login"))
  except Exception as e:
    flash("Ocurrio un error al registrar el usuario. Intentalo de nuevo.", category="danger")
    return redirect(url_for("register"))

@app.route("/login")
def login():
  return "Hello"