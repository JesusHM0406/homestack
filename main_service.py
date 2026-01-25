from models import User, Category, TypeEnum, Transaction
from extensions import db
from datetime import datetime, timezone, date
from flask_login import current_user
import json

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