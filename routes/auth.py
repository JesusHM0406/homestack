from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user, logout_user
from auth_service import register_user, services_login_user

bp = Blueprint("auth", __name__)

@bp.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    try:
      register_user(request.form)
      
      flash("¡Registro exisotso! Ya puedes iniciar sesión", "success")
      
      return redirect(url_for("auth.login"))
    except ValueError as e:
      flash(f"{e}", "danger")
      return redirect(url_for("auth.register"))
  
  return render_template("auth/register.html", user=current_user)

@bp.route("/login", methods=["GET", "POST"])
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

@bp.route("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for("auth.login"))
