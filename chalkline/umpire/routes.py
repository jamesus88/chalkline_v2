from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.events import Event, Filter
from chalkline.core.league import League

umpire = Blueprint('umpire', __name__)

@umpire.route('/schedule', methods=['GET', 'POST'])
def schedule():
    mw = svr.authorized_only('umpire')
    if mw: return mw

    res = svr.obj()
    filters = Filter.default()

    if request.method == 'POST':
        filters = Filter.parse(request.form)
        if request.form.get('add_game'):
            eventId, pos = request.form['add_game'].split('_')
            try:
                res['msg'] = Event.add_umpire(res['league'], eventId, res['user'], pos)
            except (ValueError, PermissionError) as e:
                res['msg'] = e

    filters['umpires_only'] = True
    events = Event.get(res['league'], filters=filters)

    return render_template("umpire/schedule.html", res=res, events=events, filters=filters)

@umpire.route('/assignments', methods=['GET', 'POST'])
def assignments():
    mw = svr.authorized_only('umpire')
    if mw: return mw

    res = svr.obj()
    filters = Filter.default()

    if request.method == 'POST':
        filters = Filter.parse(request.form)

        if request.form.get('substitute'):
            eventId = request.form['substitute']
            return redirect(url_for('view_info.event', eventId=eventId))

        elif request.form.get('remove'):
            pos, eventId = request.form['remove'].split('_')
            try: 
                Event.remove_umpire(eventId, pos, res['user'])
            except ValueError as e:
                res['msg'] = e
            else:
                res['msg'] = "Game successfully removed!"


    events = Event.get(res['league'], res['user'], check_user_teams=False, filters=filters)
    return render_template("umpire/assignments.html", res=res, events=events, filters=filters)