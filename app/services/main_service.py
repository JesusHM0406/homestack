import json
from app.models import Category, Transaction
from app.models.type_enum import TypeEnum
from app.extensions import db
from datetime import datetime, timezone, date
from dateutil.relativedelta import relativedelta
from flask_login import current_user
from sqlalchemy.orm import joinedload
from app.filters import format_date_spanish

def get_index_data():
  today = date.today()
  user = current_user
  
  # OBTAIN MONTHLY INCOME
  
  monthly_income_stmt = (
    db.select(db.func.sum(Transaction.amount))
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
    db.select(db.func.sum(Transaction.amount))
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
      db.func.sum(Transaction.amount).label("total")
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
      db.func.sum(Transaction.amount).label("total")
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
  
  return {
    "bal": balance,
    "mon_inc": monthly_incomes,
    "mon_exp": monthly_expenses,
    "exp_cat_analysis": expenses_cat_analysis,
    "inc_cat_analysis": income_cat_analysis,
    "inc_cats":income_cats,
    "exp_cats":expense_cats,
    "mov": last_mov,
    "today": today
  }


def create_new_transaction(form):
  MAX_CONCEPT_SIZE = 100
  
  transaction_type = form.get("transaction_type")
  category_id = form.get("category")
  concept = form.get("concept")
  amount = form.get("amount")
  date_val = form.get("date")
  
  if not transaction_type or not category_id or not concept or not amount or not date_val:
    raise ValueError("Todos los campos son obligatorios")
  
  if transaction_type not in [TypeEnum.INCOME.value, TypeEnum.EXPENSE.value]:
    raise ValueError("Tipo de transacción inválido, intenta de nuevo")

  if len(concept) > MAX_CONCEPT_SIZE:
    raise ValueError("El concepto excede el limite de tamaño, intenta reducirlo")
  
  try:
    amount = float(amount)
    if amount < 0.5:
      raise ValueError
  except ValueError:
    raise ValueError("Monto inválido, asegurate de ingresar un número mayor o igual a 0.5")
  
  try:
    category_id = int(category_id)
  except ValueError:
    raise ValueError("Ocurrió un error con la categoría, por favor intenta de nuevo")
  
  try:
    transaction_date = date.fromisoformat(date_val)
  except ValueError as e:
    raise ValueError("Formato de fecha inválido")
  
  user = current_user
  
  # Instantiate the transaction type so that the database can compare a TypeEnum with another TypeEnum
  type_enum = TypeEnum(transaction_type)
  
  category = db.session.execute(
    db.select(Category)
    .where(Category.id == category_id, Category.user_id == user.id, Category.type == type_enum)
  ).scalar_one_or_none()
  
  if not category:
    raise ValueError("Parece que la categoría no existe")
  
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
  except Exception as e:
    db.session.rollback()
    raise ValueError("Ocurrió un error al guardar la transacción")
  
  return


def handle_update_categories(form):
  cat_type = form.get("categories_type")
  added_cat = form.get("added_categories")
  deleted_cat = form.get("deleted_categories")
    
  if not cat_type or cat_type not in [TypeEnum.INCOME.value, TypeEnum.EXPENSE.value]: 
    raise ValueError("El tipo es inválido")
  
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
    raise ValueError("No se hizo ningún cambio en las categorias")
  
  if added_cat_error or deleted_cat_error:
    raise ValueError("Ocurrió un error al procesar las categorias")
  
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
  except Exception as e:
    db.session.rollback()
    print(f"DEBUG: {e}")
    raise ValueError("Error Crítico: No se realizaron cambios para proteger tus datos")
  
  return


def handle_history(args):
  user = current_user
  type_f = args.get("filter", "all")
  cat_f = args.get("cat_id", type=int)
  page = args.get("page", 1)
  
  total_income = db.session.execute(db.select(db.func.sum(Transaction.amount)).where(Transaction.user_id == user.id, Transaction.type == TypeEnum.INCOME)).scalar() or 0
  
  total_expense = db.session.execute(db.select(db.func.sum(Transaction.amount)).where(Transaction.user_id == user.id, Transaction.type == TypeEnum.EXPENSE)).scalar() or 0
  
  total_balance = total_income - total_expense
  
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
      raise ValueError("Categoría inválida")
    
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
  
  return {
    "page": pagination,
    "type_f": type_f,
    "category": current_cat,
    "categories": available_categories,
    "bal": total_balance,
    "inc": total_income,
    "exp": total_expense
  }


def handle_reports(args):
  user = current_user
  today = datetime.now(timezone.utc)
  
  date_filt = args.get("date")
  target_date = today
  if date_filt:
    try:
      target_date = datetime.strptime(date_filt, "%Y-%m-%d")
    except ValueError as e:
      raise ValueError("Formato de fecha inválido.")
  
  monthly_exp_data = db.session.execute(
    db.select(
      db.case((Transaction.category_id != None, Category.name), else_="Sin categoría").label("name"),
      db.func.sum(Transaction.amount).label("total")
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
    parsed_date = datetime(int(row.year), int(row.month), 1)
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
  
  return {
    "mon_ev": final_ev_data,
    "tranc_dates": formatted_dates,
    "mon_exp": monthly_exp_parsed,
    "date_f": target_date,
    "today": today
  }