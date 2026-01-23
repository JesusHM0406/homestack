import os

from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, money_filter, format_date_spanish
from models import User, Category, Transaction, TypeEnum
from extensions import db
from sqlalchemy import func
from datetime import date
import json

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

app.jinja_env.filters['money'] = money_filter
app.jinja_env.filters['date_es'] = format_date_spanish

@app.route("/")
@login_required
def index():
  user_id = session.get("user_id")
  
  user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one_or_none()
  
  if not user:
    flash("Ocurrio un error, por favor intenta iniciar sesión de nuevo")
    return redirect(url_for("login"))
  
  # GET BALANCE
  
  balance_stmt = (
    db.select(
      func.sum(
        db.case((Transaction.type == TypeEnum.INCOME, Transaction.amount), else_=0)
      ) -
      func.sum(
        db.case((Transaction.type == TypeEnum.EXPENSE, Transaction.amount), else_=0)
      )
    )
    .where(Transaction.user_id == user_id)
  )

  balance = db.session.execute(balance_stmt).scalar() or 0
  
  # OBTAIN MONTHLY INCOME
  
  today = date.today()
  
  monthly_income_stmt = (
    db.select(
      func.sum(
        db.case((Transaction.type == TypeEnum.INCOME, Transaction.amount), else_=0)
      )
    )
    .where(
      Transaction.user_id == user_id,
      db.extract("month", Transaction.date) == today.month,
      db.extract("year", Transaction.date) == today.year
    )
  )
  
  monthly_incomes = db.session.execute(monthly_income_stmt).scalar() or 0
  
  # OBTAIN MONTHLY EXPENSES
  
  monthly_expenses_stmt = (
    db.select(
      func.sum(
        db.case((Transaction.type == TypeEnum.EXPENSE, Transaction.amount), else_=0)
      )
    )
    .where(
      Transaction.user_id == user_id,
      db.extract("month", Transaction.date) == today.month,
      db.extract("year", Transaction.date) == today.year
    )
  )
  
  monthly_expenses = db.session.execute(monthly_expenses_stmt).scalar() or 0
  
  # OBTAIN THE INDIVIDUAL INCOME FOR EACH INCOME CATEGORY IN THE CURRENT MONTH
  
  incomes_per_cat_stmt = (
    db.select(
      db.case((Transaction.category_id != None, Category.name), else_="Sin categoría"),
      func.sum(Transaction.amount).label("total")
    )
    .select_from(Transaction)
    .outerjoin(Category, Transaction.category_id == Category.id)
    .where(
      Transaction.user_id == user_id,
      Transaction.type == TypeEnum.INCOME,
      db.extract("month", Transaction.date) == today.month,
      db.extract("year", Transaction.date) == today.year
    ).group_by(Category.name, Transaction.category_id)
  )
  
  income_cat_analysis = db.session.execute(incomes_per_cat_stmt).all()
  
  # OBTAIN THE INDIVIDUAL EXPENSES FOR EACH EXPENSE CATEGORY IN THE CURRENT MONTH
  
  expenses_per_cat_stmt = (
    db.select(
      db.case((Transaction.category_id != None, Category.name), else_="Sin categoría"),
      func.sum(Transaction.amount).label("total")
    )
    .select_from(Transaction)
    .outerjoin(Category, Transaction.category_id == Category.id)
    .where(
      Transaction.user_id == user_id,
      Transaction.type == TypeEnum.EXPENSE,
      db.extract("month", Transaction.date) == today.month,
      db.extract("year", Transaction.date) == today.year
    ).group_by(Category.name, Transaction.category_id)
  )
  
  expenses_cat_analysis = db.session.execute(expenses_per_cat_stmt).all()
  
  # OBTAIN ALL INCOME CATEGORIES
  
  income_cats_stmt = (
    db.select(Category)
    .where(
      Category.user_id == user_id,
      Category.type == TypeEnum.INCOME
    )
  )
  
  income_cats = db.session.scalars(income_cats_stmt).all()
  
  # OBTAIN ALL EXPENSE CATEGORIES
  
  expense_cats_stmt = (
    db.select(Category)
    .where(
      Category.user_id == user_id,
      Category.type == TypeEnum.EXPENSE
    )
  )
  
  expense_cats = db.session.scalars(expense_cats_stmt).all()

  # OBTAIN LAST 5 MOVEMENTS
  
  last_mov_stmt = (
    db.select(
      Transaction, 
      db.case((Transaction.category_id != None, Category.name), else_="Sin categoría")
    )
    .select_from(Transaction)
    .outerjoin(Category, Transaction.category_id == Category.id)
    .where(
      Transaction.user_id == user_id
    )
    .order_by(Transaction.date.desc())
    .limit(5)
  )

  last_mov = db.session.execute(last_mov_stmt).all()

  return render_template("index.html", username=session.get("username"), bal=balance, mon_inc=monthly_incomes, mon_exp=monthly_expenses, exp_cat_analysis=expenses_cat_analysis, inc_cat_analysis=income_cat_analysis, inc_cats=income_cats, exp_cats=expense_cats, mov=last_mov, today=today)

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
      new_user.user_categories = [
        Category(name="Comida", type=TypeEnum.EXPENSE),
        Category(name="Renta", type=TypeEnum.EXPENSE),
        Category(name="Salario", type=TypeEnum.INCOME),
        Category(name="Extra", type=TypeEnum.INCOME)
      ]
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

@app.route("/new-transaction", methods=["POST"])
@login_required
def new_transaction():
  MAX_CONCEPT_SIZE = 100
  
  transaction_type = request.form.get("transaction_type")
  category_id = request.form.get("category")
  concept = request.form.get("concept")
  amount = request.form.get("amount")
  date_val = request.form.get("date")
  
  if not transaction_type or not category_id or not concept or not amount or not date_val:
    flash("Todos los campos son obligatorios", category="danger")
    return redirect(url_for("index"))
  
  if transaction_type not in [TypeEnum.INCOME.value, TypeEnum.EXPENSE.value]:
    flash("Tipo de transacción inválido, intenta de nuevo", category="danger")
    return redirect(url_for("index"))

  if len(concept) > MAX_CONCEPT_SIZE:
    flash ("El concepto excede el limite de tamaño, intenta reducirlo", category="danger")
    return redirect(url_for("index"))
  
  try:
    amount = float(amount)
    if amount < 0.5:
      raise ValueError
  except ValueError:
    flash("Monto inválido, asegurate de ingresar un número mayor o igual a 0.5", category="danger")
    return redirect(url_for("index"))
  
  try:
    category_id = int(category_id)
  except ValueError:
    flash("Ocurrió un error con la categoría, por favor intenta de nuevo", category="danger")
    return redirect(url_for("index"))
  
  try:
    transaction_date = date.fromisoformat(date_val)
  except ValueError as e:
    flash("Formato de fecha inválido")
    return redirect(url_for("index"))
  
  user_id = session.get("user_id")
  
  # Instantiate the transaction type so that the database can compare a TypeEnum with another TypeEnum
  type_enum = TypeEnum(transaction_type)
  
  category = db.session.execute(
    db.select(Category)
    .where(Category.id == category_id, Category.user_id == user_id, Category.type == type_enum)
  ).scalar_one_or_none()
  
  if not category:
    flash("Parece que la categoría no existe", category="danger")
    return redirect(url_for("index"))
  
  try:
    new_transaction = Transaction(
      user_id=user_id,
      category_id=category.id,
      amount=amount,
      concept=concept,
      type=type_enum,
      date=transaction_date
    )
    
    db.session.add(new_transaction)
    db.session.commit()
    
    flash("¡Transacción guardada exitosamente!", category="success")
  except Exception as e:
    db.session.rollback()
    flash("Ocurrió un error al guardar la transacción", category="danger")

  return redirect(url_for("index"))

@app.route("/update-categories", methods=["POST"])
@login_required
def update_categories():
  cat_type = request.form.get("categories_type")
  added_cat = request.form.get("added_categories")
  deleted_cat = request.form.get("deleted_categories")
    
  if not cat_type or cat_type not in [TypeEnum.INCOME.value, TypeEnum.EXPENSE.value]: 
    flash("El tipo es inválido", category="danger")
    return redirect(url_for("index"))
  
  cat_type = TypeEnum(cat_type)
  
  added_cat_error = False
  deleted_cat_error = False
  
  try:
    added_cat = json.loads(added_cat)
    
    if not isinstance(added_cat, list):
      raise TypeError
  except (json.JSONDecodeError, TypeError):
    added_cat_error = True
  
  try:
    deleted_cat = json.loads(deleted_cat)
    
    if not isinstance(deleted_cat, list):
      raise TypeError
  except (json.JSONDecodeError, TypeError):
    deleted_cat_error = True
  
  if not added_cat and not deleted_cat:
    flash("No se hizo ningún cambio en las categorías", category="warning")
    return redirect(url_for("index"))
  
  if added_cat_error or deleted_cat_error:
    flash("Ocurrió un error al procesar las categorías", category="danger")
    return redirect(url_for("index"))

  user_id = session.get("user_id")
  user = db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()
  
  if not user:
    flash("Ocurrió un error al procesar tu información, intenta iniciar sesión de nuevo", category="danger")
    return redirect(url_for("login"))
  
  try:
    for cat_name in added_cat:
      new_cat = Category(user_id=user_id, name=cat_name, type=cat_type)
      db.session.add(new_cat)

    db.session.execute(
      db.update(Transaction)
      .where(Transaction.category_id.in_(deleted_cat))
      .values(category_id=None)
    )
    
    db.session.execute(
      db.delete(Category)
      .where(Category.id.in_(deleted_cat), Category.user_id == user_id)
    )
    
    db.session.commit()

    flash("Categorias actualizadas con éxito", category="success")
  except Exception as e:
    db.session.rollback()
    flash("Error Crítico: No se realizaron cambios para proteger tus datos", category="danger")
    print(f"DEBUG: {e}")
  
  return redirect(url_for("index"))

@app.route("/history")
@login_required
def history():
  user_id = session.get("user_id")
  type_f = request.args.get("filter", None)
  cat_f = request.args.get("cat_id", None)
  
  if not type_f and not cat_f:
    return render_template("history.html", type_f="all")
  
  # If there is a category id in cat_f, then we can skip type filter
  if cat_f:
    try:
      cat_id = int(cat_f)
    except ValueError as e:
      flash("Categoría inválida", "danger")
      return redirect(url_for("history", filter=type_f))
    
    category = db.session.execute(db.select(Category).where(Category.id == cat_id, Category.user_id == user_id)).scalar_one_or_none()
    
    if not category:
      flash("Categoría inválida", "danger")
      return redirect(url_for("history", filter=type_f))
  
  if type_f not in [TypeEnum.INCOME.value, TypeEnum.EXPENSE.value]:
    flash("Filtro de tipo inválido", "danger")
    return render_template("history.html", type_f="all")
  
  type_enum = TypeEnum(type_f)
  
  return render_template("history.html")