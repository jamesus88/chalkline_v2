from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.events import Event, Filter
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
    filters = Filter.default()

    if request.method == 'POST':
        filters = Filter.parse(request.form)

        if request.form.get('save'):
            Admin.update_all(request.form, Event)
            res['msg'] = 'Events updated!'
        
        elif request.form.get('delete'):
            Admin.delete(Event, request.form['delete'])
            res['msg'] = 'Event deleted.'

    events = Event.get(res['league'], filters=filters)
    league = League.get(res['league'])
    league['teams'] = Team.get_league_teams(res['league'])

    return render_template("admin/event-data.html", res=res, events=events, league=league, filters=filters)

@admin.route("/add-event", methods=['GET', 'POST'])
def add_event():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()
    league = League.get(res['league'])
    league['ump_positions'] = Event.get_all_ump_positions()

    if request.method == 'POST':
        try:
            Event.create(league, request.form)
            res['msg'] = 'Event Added!'
        except ValueError as e:
            res['msg'] = e

    return render_template("admin/add-event.html", res=res, league=league)

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
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()

    if request.method == 'POST':
        if request.form.get('delete'):
            teamId = request.form['delete']
            Team.delete(res['league'], teamId)
            res['msg'] = f"{teamId} deleted."
        elif request.form.get('save'):
            Admin.update_all(request.form, Team)
            res['msg'] = "Teams updated."


    teams = Team.get_league_teams(res['league'])
    league = League.get(res['league'])
    return render_template("admin/team-data.html", res=res, teams=teams, league=league)
    
@admin.route("/add-team", methods=['GET', 'POST'])
def add_team():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()
    league = League.get(res['league'])
    coaches = User.find_groups(res['league'], ['coach'])

    if request.method == 'POST':
        try:
            t = Team.create(league, request.form)
            res['msg'] = f"{t['teamId']} created and saved!"
        except ValueError as e:
            res['msg'] = e

    return render_template("admin/add-team.html", res=res, league=league, coaches=coaches)

@admin.route("/announcement", methods=['GET', 'POST'])
def announcement():
    pass

@admin.route("/dod-data", methods=['GET', 'POST'])
def dod_data():
    pass
    
@admin.route("/add-shift", methods=['GET', 'POST'])
def add_shift():
    pass

@admin.route("/manage-league", methods=['GET', 'POST'])
def manage_league():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()

    if request.method == 'POST':
        if request.form.get('deleteAge'):
            League.delete_age(res['league'], request.form['deleteAge'])
        elif request.form.get('addAge'):
            League.add_age(res['league'], request.form['new_age'])
        elif request.form.get('updateSeason'):
            League.update_season(res['league'], request.form['current_season'])
        


    league = League.get(res['league'])

    return render_template("admin/league.html", res=res, league=league)