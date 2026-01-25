from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from app.services import get_index_data, create_new_transaction, handle_update_categories, handle_history, handle_reports

bp = Blueprint("views", __name__)

@bp.route("/")
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

@bp.route("/new-transaction", methods=["POST"])
@login_required
def new_transaction():
  try:
    create_new_transaction(request.form)
    
    flash("¡Transacción guardada exitosamente!", category="success")
  except ValueError as e:
    flash(f"{e}", "danger")

  return redirect(url_for("views.index"))

@bp.route("/update-categories", methods=["POST"])
@login_required
def update_categories():
  try:
    handle_update_categories(request.form)

    flash("Categorias actualizadas con éxito", category="success")
  except ValueError as e:
    flash(f"{e}", category="danger")
  
  return redirect(url_for("views.index"))

@bp.route("/history")
@login_required
def history():
  try:
    data = handle_history(request.args)
  except ValueError as e:
    flash(f"{e}", "danger")
    return redirect(url_for("views.history"))
  
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

@bp.route("/reports")
@login_required
def reports():
  try:
    data = handle_reports(request.args)
  except ValueError as e:
    flash(f"{e}", "danger")
    return redirect(url_for("views.reports"))

  return render_template(
    "main/reports.html",
    user=current_user,
    mon_ev=data["mon_ev"],
    tranc_dates=data["tranc_dates"],
    mon_exp=data["mon_exp"],
    date_f=data["date_f"],
    today=data["today"]
  )