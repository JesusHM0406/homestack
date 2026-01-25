from app.models import User, Category
from app.models.type_enum import TypeEnum
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user

def register_user(form):
  MIN_PASSWORD_SIZE = 8
  
  username = form.get("username")
  password = form.get("password")
  confirm = form.get("confirm")

  # Verify that the user input is not blank
  if not username or not password or not confirm:
    raise ValueError("Todos los datos son obligatorios")

  # We need to check if that username already exists in our database since it stores unique usernames
  user_exists = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

  if user_exists:
    raise ValueError("Ya existe ese nombre de usuario, intenta con otro",)
  # We need to validate if that password contains a minimun of 8 characters for security
  if len(password) < MIN_PASSWORD_SIZE:
    raise ValueError(f"La contraseña debe contener un minimo de {MIN_PASSWORD_SIZE} caracteres")

  # If the username is correct (unique) and the password is valid, then we need to compare the password with the confirmation
  if password != confirm:
    raise ValueError("Las contraseñas no coinciden")
  
  # First we need to make the hash of the password
  password_hash = generate_password_hash(password)
  
  try:
    # Then we insert the user in the database
    new_user = User(username=username, hash=password_hash)
    # Default categories
    new_user.user_categories = [
      Category(name="Comida", type=TypeEnum.EXPENSE),
      Category(name="Renta", type=TypeEnum.EXPENSE),
      Category(name="Salario", type=TypeEnum.INCOME),
      Category(name="Extra", type=TypeEnum.INCOME)
    ]
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
  except Exception as e:
    db.session.rollback()
    raise ValueError("Ocurrió un error al registrar el usuario. Inténtalo de nuevo")
  
  return

def services_login_user(form):
  username = form.get("username")
  password = form.get("password")

  # User inputs are blank
  if not username or not password:
    raise ValueError("Debe proporcionar usuario y contraseña")

  user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

  # There is no user with that username or the password is incorrect
  if not user or not check_password_hash(user.hash, password):
    raise ValueError("Nombre de usuario y/o contraseña invalidos")
  
  login_user(user)
  
  return