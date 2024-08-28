from flask import render_template, redirect, url_for, session, request, Blueprint, abort
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
    res['league']['teams'] = Team.get_league_teams(res['league'])

    if request.method == 'POST':
        filters = Filter.parse(request.form)

        if request.form.get('save'):
            Admin.update_all(request.form, Event, res['league'])
            res['msg'] = 'Events updated!'
        
        elif request.form.get('delete'):
            Admin.delete(Event, request.form['delete'])
            res['msg'] = 'Event deleted.'

        elif request.form.get('genShifts'):
            count = Admin.generate_dod_shifts(res['league'])
            res['msg'] = f"{count} DOD shifts added!"

    events = Event.get(res['league'], filters=filters)
    

    return render_template("admin/event-data.html", res=res, events=events, filters=filters)

@admin.route("/add-event", methods=['GET', 'POST'])
def add_event():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()
    res['league']['ump_positions'] = Event.get_all_ump_positions()

    if request.method == 'POST':
        try:
            Event.create(res['league'], request.form)
            res['msg'] = 'Event Added!'
        except ValueError as e:
            res['msg'] = e

    return render_template("admin/add-event.html", res=res)

@admin.route("/user-data", methods=['GET', 'POST'])
def user_data():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()
    filters = User.Filter.default()

    if request.method == 'POST':
        filters = User.Filter.parse(request.form)

        if request.form.get('save'):
            Admin.update_all(request.form, User, res['league'])
            res['msg'] = "Users updated!"
        elif request.form.get('remove'):
            u = User.remove_league(request.form['remove'], res['league'])
            res['msg'] = f"{u['firstLast']} removed from your league."
        elif request.form.get('umpire_add_all'):
            Admin.umpire_add_all(res['league'])
            res['msg'] = "Umpire add opened."
        elif request.form.get('umpire_add_none'):
            Admin.umpire_add_none(res['league'])
            res['msg'] = "Umpire add closed."
        elif request.form.get('umpire_remove_all'):
            Admin.umpire_remove_all(res['league'])
            res['msg'] = "Umpire drop opened."
        elif request.form.get('umpire_remove_none'):
            Admin.umpire_remove_none(res['league'])
            res['msg'] = "Umpire drop closed."
        elif request.form.get('coach_add_all'):
            Admin.coach_add_all(res['league'])
            res['msg'] = "Coach add opened."
        elif request.form.get('coach_add_none'):
            Admin.coach_add_none(res['league'])
            res['msg'] = "Coach add closed."

    users = User.get(res, add_criteria={'leagues': {'$in': [res['league']['leagueId']]}}, filters=filters)
    res['league']['permissions'] = User.generate_permissions(res['league'])
    groups = User.get_all_groups()

    return render_template("admin/user-data.html", res=res, users=users, groups=groups, filters=filters)

@admin.route("/team-data", methods=['GET', 'POST'])
def team_data():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()
    filters = Team.Filter.default()

    if request.method == 'POST':
        filters = Team.Filter.parse(request.form)
        if request.form.get('delete'):
            teamId = request.form['delete']
            Team.delete(res['league'], teamId)
            res['msg'] = f"{teamId} deleted."
        elif request.form.get('save'):
            Admin.update_all(request.form, Team, res['league'])
            res['msg'] = "Teams updated."


    teams = Team.get_league_teams(res['league']['leagueId'], filters=filters)
    return render_template("admin/team-data.html", res=res, teams=teams, filters=filters)
    
@admin.route("/add-team", methods=['GET', 'POST'])
def add_team():
    mw = svr.authorized_only('admin')
    if mw: return mw

    res = svr.obj()
    coaches = User.find_groups(res['league'], ['coach'])

    if request.method == 'POST':
        try:
            t = Team.create(res['league'], request.form)
            res['msg'] = f"{t['teamId']} created and saved!"
        except ValueError as e:
            res['msg'] = e

    return render_template("admin/add-team.html", res=res, coaches=coaches)

@admin.route("/announcement", methods=['GET', 'POST'])
def announcement():
    return redirect(url_for('main.home'))

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
        elif request.form.get('updateCodes'):
            League.update_codes(res['league'], request.form)

        svr.login(res['user'], res['league']['leagueId'])
        res = svr.obj()

    return render_template("admin/league.html", res=res)