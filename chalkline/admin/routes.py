from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
from chalkline.director import director_db
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
    allTeams = db.getTeams()
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
    
    return render_template('admin/event-data.html', user=srv.safeUser(user),eventFilter=eventFilter.asdict(), eventList=eventList, allTeams=allTeams)

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

@admin.route("/announcement", methods=['GET', 'POST'])
def announcement():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    allTeams = db.getTeams()
    
    if request.method == 'POST':
        if request.form.get('updateStatus'):
            if request.form.get('sendStatusAlert'): sendAlert = True
            else: sendAlert = False
            venue = request.form['updateStatus']
            msg = db.updateFieldStatus(venue, request.form['fieldStatus'], sendAlert)
            
        if request.form.get('sendMessage'):
            groups = []
            teams = []
            if request.form.get('coach'):
                groups.append('coach')
            if request.form.get('parent'):
                groups.append('parent')
            if request.form.get('umpire'):
                groups.append('umpire')
            if request.form.get('youth'):
                groups.append('youth')
            if request.form.get('board'):
                groups.append('board')
            
            for team in allTeams:
                if request.form.get(team['teamId']):
                    teams.append(team['teamId'])
                    
            users = list(db.getUserList())

            userList = []
            for user in users:
                for group in groups:
                    if group in user['role']:
                        userList.append(user)
            
                for team in teams:
                    if team in user['teams']:
                        userList.append(user)
            
            message = request.form['msg']
            
            if len(userList) < 1:
                msg = "Error: no recipients found."
            elif 'email' not in request.form.keys() and 'phone' not in request.form.keys():
                msg = "Error: select email and/or text."
            else:
                if request.form.get('email'):
                    emailList = srv.createEmailList(userList)
                    emailList = list(dict.fromkeys(emailList))
                    srv.sendMail(body=message, recipients=emailList)
                if request.form.get('text'):
                    phoneList = srv.createPhoneList(userList)
                    phoneList = list(dict.fromkeys(phoneList))
                    srv.sendMail(body=message, recipients=phoneList)
                msg = "Message Sent!"
    
    venues = db.getVenues("Sarasota")
    
    return render_template('admin/announcement.html', user=user, msg=msg, allTeams=allTeams, venues=venues)

@admin.route("/dod-data", methods=['GET', 'POST'])
def dod_data():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    directorList = db.getUserList({'role': {'$in': ['board']}})
    hidePast = True
    msg = ''
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            if request.form['hidePast'] == 'False':
                hidePast = False
                
        if request.form.get('updateShift'):
            shiftId = request.form['updateShift']
            form = {}
            for key, value in request.form.items():
                if f'_{shiftId}' in key:
                    form[key.removesuffix(f"_{shiftId}")] = value
            msg = director_db.updateShift(shiftId, form, directorList)
            print(f"Shift: {shiftId} updated by {user['userId']}")
            
        if request.form.get('deleteShift'):
            shiftId = request.form['deleteShift']
            msg = director_db.deleteShift(shiftId)
            print(f"Shift: {shiftId} deleted by {user['userId']}")
            
    
    shiftList = director_db.getShiftList(directorList, hidePast=hidePast, user=None)
    
    return render_template('admin/dod-data.html', user=user, directorList=directorList, shiftList=shiftList, hidePast=hidePast, msg=msg)
    
@admin.route("/add-shift", methods=['GET', 'POST'])
def add_shift():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    if request.method == 'POST':
        msg = director_db.addShift(user, request.form)
        if type(msg) != str:
            return redirect(url_for('admin.dod_data'))
    
    return render_template('admin/add-shift.html', user=user, msg=msg)