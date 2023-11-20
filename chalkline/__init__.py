from flask import Flask
from flask_mail import Mail
import os

mail = Mail()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') 
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    
    mail.init_app(app)
    
    from chalkline.main.routes import main
    app.register_blueprint(main)
    
    from chalkline.teams.routes import teams
    app.register_blueprint(teams, url_prefix="/teams")
    
    from chalkline.umpire.routes import umpire
    app.register_blueprint(umpire, url_prefix="/umpire")
    
    from chalkline.league.routes import league
    app.register_blueprint(league, url_prefix="/league")
    
    from chalkline.view_info.routes import view_info
    app.register_blueprint(view_info, url_prefix="/view-info")
    
    from chalkline.invite.routes import invite
    app.register_blueprint(invite, url_prefix="/invite")
    
    from chalkline.admin.routes import admin
    app.register_blueprint(admin, url_prefix="/admin")
    
    from chalkline.docs.routes import docs
    app.register_blueprint(docs, url_prefix="/docs")
    
    from chalkline.errors.routes import errors
    app.register_blueprint(errors)
    
    from chalkline.director.routes import director
    app.register_blueprint(director, url_prefix="/director")
    
    return app