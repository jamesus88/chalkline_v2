from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chalkline14#'
    
    from chalkline.main.routes import main
    app.register_blueprint(main)
    
    from chalkline.teams.routes import teams
    app.register_blueprint(teams, url_prefix="/teams")
    
    from chalkline.umpire.routes import umpire
    app.register_blueprint(umpire, url_prefix="/umpire")
    
    return app