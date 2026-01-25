import os

from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import money_filter, format_date_spanish
from models import User, Category, Transaction, TypeEnum
from extensions import db
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from flask_migrate import Migrate
from flask_login import login_user, logout_user, LoginManager, current_user, login_required
from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta
import json

# Initialize flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Session config
app.config["SESSION_PERMANENT"] = False
# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"

db.init_app(app)
migrate = Migrate(app, db)

app.jinja_env.filters['money'] = money_filter
app.jinja_env.filters['date_es'] = format_date_spanish

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
  return db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()

@app.route("/")
@login_required
def index():
  today = datetime.now(timezone.utc)
  user = current_user
  
  # OBTAIN MONTHLY INCOME
  
  monthly_income_stmt = (
    db.select(func.sum(Transaction.amount))
    .where(
      Transaction.user_id == user.id,
      Transaction.type == TypeEnum.INCOME,
      db.extract("month", Transaction.date) == today.month,
      db.extract("year", Transaction.date) == today.year
    )
  )
  
  monthly_incomes = db.session.execute(monthly_income_stmt).scalar() or 0
  
  # OBTAIN MONTHLY EXPENSES
  
  monthly_expenses_stmt = (
    db.select(func.sum(Transaction.amount))
    .where(
      Transaction.user_id == user.id,
      Transaction.type == TypeEnum.EXPENSE,
      db.extract("month", Transaction.date) == today.month,
      db.extract("year", Transaction.date) == today.year
    )
  )
  
  monthly_expenses = db.session.execute(monthly_expenses_stmt).scalar() or 0
  
  # GET BALANCE

  balance = monthly_incomes - monthly_expenses
  
  # OBTAIN THE INDIVIDUAL INCOME FOR EACH INCOME CATEGORY IN THE CURRENT MONTH
  
  incomes_per_cat_stmt = (
    db.select(
      db.case((Transaction.category_id != None, Category.name), else_="Sin categoría"),
      func.sum(Transaction.amount).label("total")
    )
    .select_from(Transaction)
    .outerjoin(Category, Transaction.category_id == Category.id)
    .where(
      Transaction.user_id == user.id,
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
      Transaction.user_id == user.id,
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
      Category.user_id == user.id,
      Category.type == TypeEnum.INCOME
    )
  )
  
  income_cats = db.session.scalars(income_cats_stmt).all()
  
  # OBTAIN ALL EXPENSE CATEGORIES
  
  expense_cats_stmt = (
    db.select(Category)
    .where(
      Category.user_id == user.id,
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
      Transaction.user_id == user.id
    )
    .order_by(Transaction.date.desc())
    .limit(5)
  )

  last_mov = db.session.execute(last_mov_stmt).all()

  return render_template(
    "index.html",
    user=current_user,
    bal=balance,
    mon_inc=monthly_incomes,
    mon_exp=monthly_expenses,
    exp_cat_analysis=expenses_cat_analysis,
    inc_cat_analysis=income_cat_analysis,
    inc_cats=income_cats,
    exp_cats=expense_cats,
    mov=last_mov,
    today=today
  )

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

      login_user(new_user)

      # Redirect user to login page
      return redirect(url_for("login"))
    except Exception as e:
      db.session.rollback()
      flash("Ocurrio un error al registrar el usuario. Intentalo de nuevo", category="danger")
      return redirect(url_for("register"))
  
  return render_template("register.html", user=current_user)

@app.route("/login", methods=["GET", "POST"])
def login():
  # Clear all sessions before log in
  logout_user()

  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")

    # User inputs are blank
    if not username or not password:
      flash("Debe proporcionar usuario y contraseña", category="danger")
      return render_template("login.html", user=current_user)

    user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()

    # There is no user with that username or the password is incorrect
    if not user or not check_password_hash(user.hash, password):
      flash("Nombre de usuario y/o contraseña invalidos", category="danger")
      return render_template("login.html", user=current_user)
    
    # Login user
    login_user(user)

    return redirect("/")
  
  return render_template("login.html", user=current_user)

@app.route("/logout")
@login_required
def logout():
  logout_user()
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
  
  user = current_user
  
  # Instantiate the transaction type so that the database can compare a TypeEnum with another TypeEnum
  type_enum = TypeEnum(transaction_type)
  
  category = db.session.execute(
    db.select(Category)
    .where(Category.id == category_id, Category.user_id == user.id, Category.type == type_enum)
  ).scalar_one_or_none()
  
  if not category:
    flash("Parece que la categoría no existe", category="danger")
    return redirect(url_for("index"))
  
  try:
    new_transaction = Transaction(
      user_id=user.id,
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
  
  user = current_user
  
  try:
    for cat_name in added_cat:
      new_cat = Category(user_id=user.id, name=cat_name, type=cat_type)
      db.session.add(new_cat)

    db.session.execute(
      db.update(Transaction)
      .where(Transaction.category_id.in_(deleted_cat))
      .values(category_id=None)
    )
    
    db.session.execute(
      db.delete(Category)
      .where(Category.id.in_(deleted_cat), Category.user_id == user.id)
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
  user = current_user
  type_f = request.args.get("filter", "all")
  cat_f = request.args.get("cat_id", type=int)
  page = request.args.get("page", 1)
  
  total_income = db.session.execute(db.select(func.sum(Transaction.amount)).where(Transaction.user_id == user.id, Transaction.type == TypeEnum.INCOME)).scalar() or 0
  
  total_expense = db.session.execute(db.select(func.sum(Transaction.amount)).where(Transaction.user_id == user.id, Transaction.type == TypeEnum.EXPENSE)).scalar() or 0
  
  total_balance = total_income -total_expense
  
  try:
    page = int(page)
    
    if page <= 0:
      raise ValueError
  except ValueError as e:
    page = 1
  
  query = db.select(Transaction).options(joinedload(Transaction.category)).where(Transaction.user_id == user.id).order_by(Transaction.date.desc())
  
  current_cat = None
  available_categories = []
  
  # If there is a category id in cat_f, then we can skip type filter
  if cat_f:
    current_cat = db.session.execute(db.select(Category).where(Category.id == cat_f, Category.user_id == user.id)).scalar_one_or_none()
    
    if not current_cat:
      flash("Categoría inválida", "danger")
      return redirect(url_for("history"))
    
    query = query.where(Transaction.category_id == cat_f)
    
    type_f = current_cat.type.value
    available_categories = db.session.scalars(db.select(Category).where(Category.user_id == user.id, Category.type == current_cat.type)).all()
  
  # If there is no cat_id parameter, then we filter by type
  elif type_f in [TypeEnum.INCOME.value, TypeEnum.EXPENSE.value]:
    type_enum = TypeEnum(type_f)
    
    query = query.where(Transaction.type == type_enum)
    
    available_categories = db.session.scalars(db.select(Category).where(Category.user_id == user.id, Category.type == type_enum)).all()
    
  else:
    type_f = "all"
    
    available_categories = db.session.scalars(db.select(Category).where(Category.user_id == user.id)).all()
  
  pagination = db.paginate(query, page=page, per_page=20, error_out=False)
  
  return render_template(
    "history.html",
    user=current_user,
    page=pagination,
    type_f=type_f,
    category=current_cat,
    categories=available_categories,
    bal=total_balance,
    inc=total_income,
    exp=total_expense
  )

@app.route("/reports")
def reports():
  user = current_user
  today = datetime.now(timezone.utc)
  
  date_filt = request.args.get("date")
  target_date = today
  if date_filt:
    try:
      target_date = datetime.strptime(date_filt, "%Y-%m-%d")
    except ValueError as e:
      flash("Formato de fecha inválido", "danger")
  
  monthly_exp_data = db.session.execute(
    db.select(
      db.case((Transaction.category_id != None, Category.name), else_="Sin categoría").label("name"),
      func.sum(Transaction.amount).label("total")
    )
    .select_from(Transaction)
    .outerjoin(Category, Transaction.category_id == Category.id)
    .where(
      Transaction.user_id == user.id,
      Transaction.type == TypeEnum.EXPENSE,
      db.extract("year", Transaction.date) == target_date.year,
      db.extract("month", Transaction.date) == target_date.month
    ).group_by(Category.name, Transaction.category_id)
  ).all()

  monthly_exp_parsed = [{"name": row.name, "total": float(row.total)} for row in monthly_exp_data]

  start_date = (today - relativedelta(months=6)).replace(day=1)
  
  monthly_ev_query = (
    db.select(
      db.func.sum(db.case((Transaction.type == TypeEnum.INCOME, Transaction.amount), else_= 0)).label("income"),
      db.func.sum(db.case((Transaction.type == TypeEnum.EXPENSE, Transaction.amount), else_= 0)).label("expense"),
      db.extract("year", Transaction.date).label("year"),
      db.extract("month", Transaction.date).label("month")
    )
    .where(
      Transaction.user_id == user.id,
      Transaction.date >= start_date
    )
    .group_by("year", "month")
    .order_by("year", "month")
  )
  
  monthly_ev = db.session.execute(monthly_ev_query).all()
  
  data_map = {}
  
  pointer_date = start_date
  while pointer_date <= today:
    key = (pointer_date.year, pointer_date.month)
    data_map[key] = {
      "income": 0,
      "expense": 0,
      "balance": 0,
      "year": pointer_date.year,
      "month": pointer_date.month
    }
    pointer_date += relativedelta(months=1)
  
  for row in monthly_ev:
    key = (int(row.year), int(row.month))
    if key in data_map:
      inc = float(row.income)
      exp = float(row.expense)
      data_map[key]["income"] = inc
      data_map[key]["expense"] = exp
      data_map[key]["balance"] = inc - exp
  
  final_ev_data = list(data_map.values())
  
  transaction_dates_query = (
    db.select(
      db.extract("year", Transaction.date).label("year"),
      db.extract("month", Transaction.date).label("month")
    )
    .where(
      Transaction.user_id == user.id
    )
    .group_by("year", "month")
    .order_by(db.desc("year"), db.desc("month"))
  )
  
  transaction_dates = db.session.execute(transaction_dates_query).all()
  
  formatted_dates = []
  for row in transaction_dates:
    parsed_date = datetime(row.year, row.month, 1)
    formatted_dates.append({
      "year": int(row.year),
      "month": int(row.month),
      "iso-date": f"{row.year}-{row.month}-{parsed_date.day}",
      "formatted": format_date_spanish(parsed_date, short=True),
      "obj": parsed_date
    })

  target_date = {
    "iso-date": f"{target_date.year}-{target_date.month}-1",
    "formatted": format_date_spanish(target_date, short=True)
  }

  return render_template(
    "reports.html",
    user=current_user,
    mon_ev=final_ev_data,
    tranc_dates=formatted_dates,
    mon_exp=monthly_exp_parsed,
    date_f=target_date,
    today=today
  )