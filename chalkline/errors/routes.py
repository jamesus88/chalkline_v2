from flask import render_template, abort, Blueprint, session
import traceback
from chalkline import server as srv
import chalkline.logger as Logger

errors = Blueprint('errors', __name__)

@errors.route("/abort/<i>")
def create_error(i: int = 500):
    abort(int(i))

@errors.app_errorhandler(404)
def _404(error):
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("errors/404.html", user=user, error=error, sobj=sobj), 404

@errors.app_errorhandler(500)
def _500(error):
    user = srv.getUser()
    print(traceback.format_exc())
    sobj=srv.getSessionObj(session)

    return render_template("errors/500.html", user=user, error=error, sobj=sobj), 500

@errors.app_errorhandler(PermissionError)
def permission_error(error):
    user = srv.getUser()
    print(error)
    sobj=srv.getSessionObj(session)

    return render_template("errors/generic.html", user=user, error=error, sobj=sobj), 403

@errors.app_errorhandler(Exception)
def generic(error):
    user = srv.getUser()
    print(traceback.format_exc())
    sobj=srv.getSessionObj(session)

    return render_template("errors/generic.html", user=user, error=error, sobj=sobj), 400
