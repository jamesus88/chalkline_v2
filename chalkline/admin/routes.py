from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
admin = Blueprint('admin', __name__)

@admin.route("/events", methods=['GET','POST'])
def event_data():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.event_data'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    eventFilter = get_events.EventFilter()
    teamsList = db.getTeams()
    userList = db.getUserList()
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
            
        if request.form.get('updateEvent'):
            eventId = request.form['updateEvent']
            this_event = db.getEventInfo(eventId)
            form = {}
            for key, value in request.form.items():
                if f'_{eventId}' in key:
                    form[key.removesuffix(f"_{eventId}")] = value
            
            msg = db.updateEvent(this_event, form, userList)
            print(f"Event: {eventId} updated by {user['userId']}")
            
        elif request.form.get('deleteEvent'):
            eventId = request.form['deleteEvent']
            msg = db.deleteEvent(eventId)
            print(f"Event: {eventId} deleted by {user['userId']}")

    eventList = get_events.getEventList(eventFilter)
    
    return render_template('admin/event-data.html', user=srv.safeUser(user),eventFilter=eventFilter.asdict(), eventList=eventList, teamsList=teamsList)

@admin.route("/add-event", methods=['GET', 'POST'])
def add_event():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    teamsList = db.getTeams()
    userList = db.getUserList()
    
    if request.method == 'POST':
        msg = db.addEvent(user, request.form)
        if type(msg) != str:
            return redirect(url_for('admin.event_data'))
    
    return render_template("admin/add-event.html", user=user, msg=msg, userList=userList, teamsList=teamsList)

@admin.route("/team-data", methods=['GET', 'POST'])
def team_data():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    ageGroupFilter = "None" 
    
    if request.method == 'POST':
        if request.form.get('ageGroupFilter'):
            ageGroupFilter = request.form['ageGroupFilter']
        
        if request.form.get('updateTeam'):
            teamId = request.form['updateTeam']
            this_team = db.getTeamInfo(teamId)
            form = {}
            for key, value in request.form.items():
                if f'_{teamId}' in key:
                    form[key.removesuffix(f"_{teamId}")] = value
            msg = db.updateTeam(this_team, form)
            print(f"Team: {teamId} updated by {user['userId']}")
            
        elif request.form.get('deleteTeam'):
            teamId = request.form['deleteTeam']
            msg = db.deleteTeam(teamId)
            print(f"Team: {teamId} deleted by {user['userId']}")
    
    criteria = {}
    if ageGroupFilter != 'None':
        criteria['teamAgeGroup'] = ageGroupFilter
        
    teamsList = db.getTeams(criteria)
    
    return render_template("admin/team-data.html", user=user, teamsList=teamsList, ageGroupFilter=ageGroupFilter, msg=msg)
    
@admin.route("/add-team", methods=['GET', 'POST'])
def add_team():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    if request.method == 'POST':
        msg = db.addTeam(user, request.form)
        if type(msg) != str:
            return redirect(url_for('admin.team_data'))
    
    return render_template("admin/add-team.html", user=user, msg=msg)



@admin.route("/user-data", methods=['GET', 'POST'])
def user_data():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    userList = db.getUserList()