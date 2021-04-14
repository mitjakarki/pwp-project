import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from nearbyEvents.constants import *

db = SQLAlchemy()
app = None
# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified for Flask SQLAlchemy
def create_app(test_config=None):
    #db = SQLAlchemy()
    app = Flask(__name__, instance_relative_config=True)
    
    if test_config is None:
        app.config.from_mapping(
        SECRET_KEY="password",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    else:
        app.config.from_mapping(test_config)
        
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    db.init_app(app)
    
    from . import models
    from . import api
    app.cli.add_command(models.initializeDatabase)
    app.cli.add_command(models.generateTestDatabase)
    app.register_blueprint(api.api_bp)
    
    @app.route(LINK_RELATIONS_URL)
    def send_link_relations():
        return "link relations"
        
    @app.route("/profiles/<profile>/")
    def send_profile(profile):
        return "you requests {} profile".format(profile)
        
    @app.route("/admin/")
    def admin_site():
        return app.send_static_file("html/admin.html")
        
    return app

#app=create_app()