import os

import click
import flask
from flask import Flask
from flask import current_app
from flask import redirect
from flask import render_template
from flask import url_for
from flask import request
from flask.cli import load_dotenv
from flask_login import AnonymousUserMixin
from flask_login import UserMixin
from flask_login import current_user

from flask_admin import Admin
from flask_admin.contrib import sqla as flask_admin_sqla
from flask_admin import AdminIndexView
from flask_admin import expose
from flask_admin.menu import MenuLink

from auth_views import auth_blueprint
from secret_views import secret_blueprint
from init import db
from init import login_manager
from init import migrate
from models import User


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


from config import DevelopmentConfig
from config import ProductionConfig
from config import TestingConfig

profiles = {
    'development': DevelopmentConfig(),
    'production': ProductionConfig(),
    'testing': TestingConfig()
}



#
# Flask admin setup
#


class DefaultModelView(flask_admin_sqla.ModelView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for("home", next=request.url))


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for("home", next=request.url))

    @expose("/")
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for("home"))
        return super(MyAdminIndexView, self).index()

    @expose("/dashboard")
    def indexs(self):
        if not current_user.is_authenticated:
            return redirect(url_for("home"))
        return super(MyAdminIndexView, self).index()



def create_app(profile):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(profiles[profile])
    app.config.from_pyfile("config.py", silent=True)


    app.register_blueprint(auth_blueprint)
    app.register_blueprint(secret_blueprint)


    admin = Admin(
        app,
        name="My App",
        template_mode="bootstrap4",
        index_view=MyAdminIndexView(),
    )
    admin.add_view(DefaultModelView(User, db.session))
    admin.add_link(
        MenuLink(name="Logout", category="", url="/auth/logout")
    )



    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    if profile != "testing":
        app.config.from_pyfile("config.py", silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.shell_context_processor
    def shell():
        return {
            "db": db,
            "User": User
        }


    @app.route('/')
    def home():
        # --- demo purposes --
        try:
            db.create_all()
        except:
            pass 

        try:
            u = db.session.query(User).filter_by(email='admin@domain.com').first()
            if u is None:
                u = User(email='admin@domain.com')
                u.password = 'pass'
                db.session.add(u)
                db.session.commit()
        except: 
            pass
        return render_template('home.html')

    return app


flask_env = os.environ.get("FLASK_ENV", default="development")
app = create_app(flask_env)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True, ssl_context='adhoc')