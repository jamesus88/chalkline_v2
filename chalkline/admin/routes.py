from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.events import Event
from chalkline.core.league import League
from chalkline.core.team import Team
from chalkline.core.user import User

from .admin import Admin

admin = Blueprint('admin', __name__)

@admin.route("/event-data", methods=['GET','POST'])
def event_data():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()

    if request.method == 'POST':
        if request.form.get('save'):
            Admin.update_all(request.form, Event)
            res['msg'] = 'Events updated!'

    events = Event.get(res['league'])
    league = League.get(res['league'])
    league['teams'] = Team.get_league_teams(res['league'])

    return render_template("admin/event-data.html", res=res, events=events, league=league)

@admin.route("/add-event", methods=['GET', 'POST'])
def add_event():
    pass

@admin.route("/user-data", methods=['GET', 'POST'])
def user_data():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()

    if request.method == 'POST':
        if request.form.get('save'):
            Admin.update_all(request.form, User)
            res['msg'] = "Users updated!"

    users = User.get({'leagues': {'$in': [res['league']]}})
    league = League.get(res['league'])
    league['permissions'] = User.generate_permissions(league, Event.get_all_ump_positions())
    groups = User.get_all_groups()

    return render_template("admin/user-data.html", res=res, users=users, league=league, groups=groups)

@admin.route("/team-data", methods=['GET', 'POST'])
def team_data():
    pass
    
@admin.route("/add-team", methods=['GET', 'POST'])
def add_team():
    pass

@admin.route("/announcement", methods=['GET', 'POST'])
def announcement():
    pass

@admin.route("/dod-data", methods=['GET', 'POST'])
def dod_data():
    pass
    
@admin.route("/add-shift", methods=['GET', 'POST'])
def add_shift():
    pass