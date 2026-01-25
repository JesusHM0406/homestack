from flask import Flask
from filters import money_filter, format_date_spanish
from models import User
from extensions import db, migrate, login_manager
from config import Config
from routes import auth, views

# Initialize flask app
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)

app.jinja_env.filters['money'] = money_filter
app.jinja_env.filters['date_es'] = format_date_spanish

@login_manager.user_loader
def load_user(user_id):
  return db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()

app.register_blueprint(auth.bp)
app.register_blueprint(views.bp)