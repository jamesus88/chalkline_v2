from flask import render_template, abort, Blueprint
import traceback
from chalkline import server as srv
errors = Blueprint('errors', __name__)

@errors.route("/abort/<i>")
def create_error(i: int = 500):
    abort(int(i))

@errors.app_errorhandler(404)
def _404(error):
    user = srv.getUser()
    return render_template("errors/404.html", user=user, error=error)

@errors.app_errorhandler(500)
def _500(error):
    user = srv.getUser()
    return render_template("errors/500.html", user=user, error=error)

@errors.app_errorhandler(Exception)
def generic(error):
    user = srv.getUser()
    print(traceback.format_exc())
    return render_template("errors/generic.html", user=user, error=error)
