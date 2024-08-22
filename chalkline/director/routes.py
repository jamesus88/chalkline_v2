from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.director import Shift, Filter

director = Blueprint('director', __name__)

@director.route("/schedule", methods=['GET', 'POST'])
def schedule():
    mw = svr.authorized_only('director')
    if mw: return mw

    res = svr.obj()
    filters = Filter.default()

    if request.method == 'POST':
        filters = Filter.parse(request.form)

        if request.form.get('add'):
            Shift.add_director(request.form['add'], res['user'])

        elif request.form.get('delete'):
            Shift.delete(request.form['delete'])

    shifts = Shift.get(res['league'], filters=filters)

    return render_template("director/schedule.html", res=res, shifts=shifts, filters=filters)

@director.route("/shifts", methods=['GET', 'POST'])
def shifts():
    mw = svr.authorized_only('director')
    if mw: return mw

    res = svr.obj()
    filters = Filter.default()

    if request.method == 'POST':
        filters = Filter.parse(request.form)

        if request.form.get('remove'):
            Shift.remove_director(request.form['remove'])

    shifts = Shift.get(res['league'], user=res['user'], filters=filters)

    return render_template("director/shifts.html", res=res, shifts=shifts, filters=filters)