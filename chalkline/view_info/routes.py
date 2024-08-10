from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.events import Event
from chalkline.core.user import User
from chalkline.core.league import League

view_info = Blueprint('view_info', __name__)

@view_info.route("/event/<eventId>", methods=['GET', 'POST'])
def event(eventId):
    mw = svr.authorized_only()
    if mw: return mw

    res = svr.obj()
    e = Event.find(eventId)
    e['league_info'] = League.get(e['leagueId'])
    all_umpires = User.find_groups(res['league'], ['umpire'])
    edit_view = False

    if request.method == 'POST':
        if request.form.get('edit'):
            edit_view = True
        elif request.form.get('cancel'):
            pass
        elif request.form.get('save'):
            Event.update(e, request.form)
            edit_view = False
            res['msg'] = "Saved!"
        elif request.form.get('delete_umpire'):
            Event.delete_ump_pos(e, request.form['delete_umpire'])
            res['msg'] = f"{request.form['delete_umpire']} position deleted."
        elif request.form.get('add_umpire'):
            Event.add_ump_pos(e, request.form['pos'])
            res['msg'] = f"{request.form['pos']} position added."
        
        # reload event
        e = Event.find(eventId)
        e['league_info'] = League.get(e['leagueId'])

    return render_template("view_info/event.html", res=res, edit_view=edit_view, event=e, all_umpires=all_umpires)

@view_info.route("/user/<userId>", methods=['GET', 'POST'])
@view_info.route("/user")
def user(userId=None):
    pass