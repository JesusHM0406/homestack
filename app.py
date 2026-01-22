import os

from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
from models import User, Category, Transaction, TypeEnum
from extensions import db
from sqlalchemy import func
from datetime import date

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

@app.template_filter('money')
def money_filter(value):
  if value < 0:
    return "-${:,.2f}".format(float(abs(value)))
  return "${:,.2f}".format(float(value))

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
        db.case((Category.type == TypeEnum.INCOME, Transaction.amount), else_=0)
      ) -
      func.sum(
        db.case((Category.type == TypeEnum.EXPENSE, Transaction.amount), else_=0)
      )
    )
    .join(Category)
    .where(Transaction.user_id == user_id)
  )

  balance = db.session.execute(balance_stmt).scalar() or 0
  
  # OBTAIN MONTHLY INCOME
  
  now = date.today()
  
  monthly_income_stmt = (
    db.select(func.sum(Transaction.amount))
    .join(Category)
    .where(
      Transaction.user_id == user_id,
      Category.type == TypeEnum.INCOME,
      db.extract("month", Transaction.date) == now.month,
      db.extract("year", Transaction.date) == now.year
    )
  )
  
  monthly_incomes = db.session.execute(monthly_income_stmt).scalar() or 0
  
  # OBTAIN MONTHLY EXPENSES
  
  monthly_expenses_stmt = (
    db.select(func.sum(Transaction.amount))
    .join(Category)
    .where(
      Transaction.user_id == user_id,
      Category.type == TypeEnum.EXPENSE,
      db.extract("month", Transaction.date) == now.month,
      db.extract("year", Transaction.date) == now.year
    )
  )
  
  monthly_expenses = db.session.execute(monthly_expenses_stmt).scalar() or 0
  
  # OBTAIN THE INDIVIDUAL INCOME FOR EACH INCOME CATEGORY IN THE CURRENT MONTH
  
  incomes_per_cat_stmt = (
    db.select(
      Category.name,
      func.sum(Transaction.amount).label("total")
    )
    .join(Transaction)
    .where(
      Category.user_id == user_id,
      Category.type == TypeEnum.INCOME,
      db.extract("month", Transaction.date) == now.month,
      db.extract("year", Transaction.date) == now.year
    ).group_by(Category.name)
  )
  
  income_cat_analysis = db.session.execute(incomes_per_cat_stmt).all()
  
  # OBTAIN THE INDIVIDUAL EXPENSES FOR EACH EXPENSE CATEGORY IN THE CURRENT MONTH
  
  expenses_per_cat_stmt = (
    db.select(
      Category.name,
      func.sum(Transaction.amount).label("total")
    )
    .join(Transaction)
    .where(
      Category.user_id == user_id,
      Category.type == TypeEnum.EXPENSE,
      db.extract("month", Transaction.date) == now.month,
      db.extract("year", Transaction.date) == now.year
    ).group_by(Category.name)
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
    db.select(Transaction, Category)
    .join(Category)
    .where(
      Transaction.user_id == user_id
    )
    .order_by(Transaction.date.desc())
    .limit(5)
  )

  last_mov = db.session.execute(last_mov_stmt).all()

  return render_template("index.html", username=session.get("username"), bal=balance, mon_inc=monthly_incomes, mon_exp=monthly_expenses, exp_cat_analysis=expenses_cat_analysis, inc_cat_analysis=income_cat_analysis, inc_cats=income_cats, exp_cats=expense_cats, mov=last_mov)

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
  
  if not transaction_type or not category_id or not concept or not amount:
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
      concept=concept
    )
    
    db.session.add(new_transaction)
    db.session.commit()
    
    flash("¡Transacción guardada exitosamente!", category="success")
  except Exception:
    db.session.rollback()
    flash("Ocurrió un error al guardar la transacción", category="danger")

  return redirect(url_for("index"))