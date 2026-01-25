import os

from flask import Flask, render_template, redirect, request, flash, url_for
from helpers import money_filter, format_date_spanish
from models import User
from extensions import db
from flask_migrate import Migrate
from flask_login import logout_user, LoginManager, current_user, login_required
from auth_service import register_user, services_login_user
from main_service import get_index_data, create_new_transaction, handle_update_categories, handle_history, handle_reports

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
  try:
    data = handle_reports(request.args)
  except ValueError as e:
    flash(f"{e}", "danger")
    return redirect(url_for("reports"))

  return render_template(
    "main/reports.html",
    user=current_user,
    mon_ev=data["mon_ev"],
    tranc_dates=data["tranc_dates"],
    mon_exp=data["mon_exp"],
    date_f=data["date_f"],
    today=data["today"]
  )