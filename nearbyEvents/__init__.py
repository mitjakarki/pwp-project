import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

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
    app.cli.add_command(models.initializeDatabase)
    app.cli.add_command(models.generateTestDatabase)
    
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
        
    return app

#app=create_app()