from flask import redirect, url_for, session
from functools import wraps

def login_required(f):
  
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if session.get("user_id") is None:
      return redirect(url_for("login"))
    return f(*args, **kwargs)
  return decorated_function

def money_filter(value):
  if value < 0:
    return "-${:,.2f}".format(float(abs(value)))
  return "${:,.2f}".format(float(value))

def format_date_spanish(date):
  months = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
  }
  
  day = date.day
  month = months[date.month]
  year = date.year
  
  return f"{day} de {month} de {year}"