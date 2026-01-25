from flask import Flask
from app.config import Config

# Initialize flask app
def create_app():
  app = Flask(__name__)
  app.config.from_object(Config)

  from app.extensions import db, migrate, login_manager
  from app.models import User
  from app.routes import auth, views
  from app.filters import money_filter, format_date_spanish

  db.init_app(app)
  migrate.init_app(app, db)
  login_manager.init_app(app)

  @login_manager.user_loader
  def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()

  login_manager.login_view = 'auth.login'
  login_manager.login_message = 'Por favor inicia sesión para acceder.'
  login_manager.login_message_category = 'warning'

  app.register_blueprint(auth.bp)
  app.register_blueprint(views.bp)
  
  app.jinja_env.filters['money'] = money_filter
  app.jinja_env.filters['date_es'] = format_date_spanish
  
  return app