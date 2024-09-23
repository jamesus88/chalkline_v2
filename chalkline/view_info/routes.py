from flask import render_template, redirect, url_for, abort, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.events import Event
from chalkline.core.user import User
from chalkline.core.league import League
from chalkline.core.team import Team

view_info = Blueprint('view_info', __name__)

@view_info.route("/event/<eventId>", methods=['GET', 'POST'])
def event(eventId):
    mw = svr.authorized_only(set_next_url=request.url)
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

        elif request.form.get('substitute'):
            sub = request.form['sub_user']
            pos = request.form['substitute']
            try:
                user, req_user = User.request_sub(res['user'], e, pos, sub)
            except ValueError as e:
                res['msg'] = e
            else:
                svr.login(user)
                res = svr.obj()
                res['msg'] = f"Request sent to {req_user['firstLast']}"
            

        
        # reload event
        e = Event.find(eventId)
        e['league_info'] = League.get(e['leagueId'])

    return render_template("view_info/event.html", res=res, edit_view=edit_view, event=e, all_umpires=all_umpires)

@view_info.route("/user/<userId>", methods=['GET', 'POST'])
@view_info.route("/user")
def user(userId=None):
    mw = svr.authorized_only(set_next_url=request.url)
    if mw: return mw

    res = svr.obj()

    if userId:
        u = User.get_user(userId=userId, view=True)
        if not u:
            abort(404)
    else:
        return redirect(url_for('main.home'))

    return render_template("view_info/user.html", res=res, user=u)

@view_info.route("/team/<teamId>", methods=['GET', 'POST'])
@view_info.route("/team")
def team(teamId=None):
    mw = svr.authorized_only(set_next_url=request.url)
    if mw: return mw

    if not teamId:
        return redirect(url_for('main.home'))

    res = svr.obj()
    all_coaches = User.find_groups(res['league'], ['coach'])

    if request.method == 'POST':
        if not res['admin']:
            raise PermissionError('This action is restricted to Admins only.')
        if request.form.get('removeCoach'):
            Team.remove_coach(teamId, res['league']['current_season'], request.form['removeCoach'])
        elif request.form.get('add'):
            Team.add_coach(teamId, res['league']['current_season'], request.form['addCoach'])
    
    team = Team.get(teamId)
    if not team:
        abort(404)
    Team.load_contacts(team)

    return render_template("view_info/team.html", res=res, team=team, all_coaches=all_coaches)
