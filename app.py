import os

from flask import Flask, render_template, redirect, request, flash, url_for
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
from auth_service import register_user, services_login_user
from main_service import get_index_data, create_new_transaction, handle_update_categories, handle_history

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
  data = get_index_data()

  return render_template(
    "main/index.html",
    user=current_user,
    bal=data["bal"],
    mon_inc=data["mon_inc"],
    mon_exp=data["mon_exp"],
    exp_cat_analysis=data["exp_cat_analysis"],
    inc_cat_analysis=data["inc_cat_analysis"],
    inc_cats=data["inc_cats"],
    exp_cats=data["exp_cats"],
    mov=data["mov"],
    today=data["today"]
  )

@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    try:
      register_user(request.form)
      
      flash("¡Registro exisotso! Ya puedes iniciar sesión", "success")
      
      return redirect(url_for("login"))
    except ValueError as e:
      flash(f"{e}", "danger")
      return redirect(url_for("register"))
  
  return render_template("auth/register.html", user=current_user)

@app.route("/login", methods=["GET", "POST"])
def login():
  # Clear all sessions before log in
  logout_user()

  if request.method == "POST":
    try:
      services_login_user(request.form)
      
      return redirect(url_for("index"))
    except ValueError as e:
      flash(f"{e}", "danger")
  
  return render_template("auth/login.html", user=current_user)

@app.route("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for("login"))

@app.route("/new-transaction", methods=["POST"])
@login_required
def new_transaction():
  try:
    create_new_transaction(request.form)
    
    flash("¡Transacción guardada exitosamente!", category="success")
  except ValueError as e:
    flash(f"{e}", "danger")

  return redirect(url_for("index"))

@app.route("/update-categories", methods=["POST"])
@login_required
def update_categories():
  try:
    handle_update_categories(request.form)

    flash("Categorias actualizadas con éxito", category="success")
  except ValueError as e:
    flash(f"{e}", category="danger")
  
  return redirect(url_for("index"))

@app.route("/history")
@login_required
def history():
  try:
    data = handle_history(request.args)
  except ValueError as e:
    flash(f"{e}", "danger")
    return redirect(url_for("history"))
  
  return render_template(
    "main/history.html",
    user=current_user,
    page=data["page"],
    type_f=data["type_f"],
    category=data["category"],
    categories=data["categories"],
    bal=data["bal"],
    inc=data["inc"],
    exp=data["exp"]
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
    "main/reports.html",
    user=current_user,
    mon_ev=final_ev_data,
    tranc_dates=formatted_dates,
    mon_exp=monthly_exp_parsed,
    date_f=target_date,
    today=today
  )