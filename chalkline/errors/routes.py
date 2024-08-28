from flask import render_template, abort, Blueprint
import traceback
from chalkline.core import server as svr

errors = Blueprint('errors', __name__)

@errors.route("/abort/<i>")
def create_error(i: int = 500):
    abort(int(i))

@errors.app_errorhandler(404)
def _404(error):
    res = svr.obj()
    return render_template("errors/404.html", res=res, error=error), 404

@errors.app_errorhandler(500)
def _500(error):
    res = svr.obj()
    print(traceback.format_exc())
    return render_template("errors/500.html", res=res, error=error), 500

@errors.app_errorhandler(PermissionError)
def permission_error(error):
    res = svr.obj()
    return render_template("errors/generic.html", res=res, error=error), 403

@errors.app_errorhandler(Exception)
def generic(error):
    res = svr.obj()
    print(traceback.format_exc())
    return render_template("errors/generic.html", res=res, error=error), 400
