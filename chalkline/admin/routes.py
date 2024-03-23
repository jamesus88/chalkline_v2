from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events, send_mail
from chalkline import server as srv
from chalkline.director import director_db
from chalkline.admin import admin_db
admin = Blueprint('admin', __name__)

@admin.route("/event-data", methods=['GET','POST'])
def event_data():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.event_data'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    eventFilter = get_events.EventFilter({'admin': True})

    allTeams = db.getTeams()
    userList = db.getUserList()
    msg = ''
    
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
            
            msg = db.updateEvent(user, this_event, form, userList)
            
        elif request.form.get('deleteEvent'):
            eventId = request.form['deleteEvent']
            msg = db.deleteEvent(user, eventId)
            
        elif request.form.get('freeDrop'):
            if request.form['freeDrop'] == 'open':
                msg = admin_db.openFreeDrop()
            else:
                msg = admin_db.closeFreeDrop()
        
        elif request.form.get('lockGames'):
            if request.form['lockGames'] == 'open':
                msg = admin_db.unlockGames()
            else:
                msg = admin_db.lockGames()
                
        elif request.form.get('updateMisc'):
            msg = admin_db.updateMisc()

    eventList = get_events.getEventList(eventFilter)
    
    return render_template('admin/event-data.html', user=srv.safeUser(user),eventFilter=eventFilter.asdict(), eventList=eventList, allTeams=allTeams, msg=msg)

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
            msg = db.updateTeam(user, this_team, form)
            
        elif request.form.get('deleteTeam'):
            teamId = request.form['deleteTeam']
            msg = db.deleteTeam(user, teamId)
    
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
            for target in users:
                for group in groups:
                    if group in target['role']:
                        userList.append(target)
            
                for team in teams:
                    if team in target['teams']:
                        userList.append(target)
                        
            # add bcc
            if request.form.get('bcc'):
                userList.append(user)
                        
            text = request.form['msg']

            if 'file' in request.files and request.files['file'].filename != '':
                print('html uploaded')
                message = request.files['file'].read()
            else:
                print('custom message:', text)
                message = render_template("emails/announcement.html", user=user, message=text)
            if len(userList) < 1:
                msg = "Error: no recipients found."
            elif 'email' not in request.form.keys() and 'phone' not in request.form.keys():
                msg = "Error: select email and/or text."
            elif len(text) < 1 and 'file' not in request.files:
                msg = "Error: upload html or enter custom message."
            else:
                if request.form.get('email'):
                    emailList = srv.createEmailList(userList)
                    emailList = list(dict.fromkeys(emailList))
                    
                    msgList = []
                    for recipient in emailList:
                        email = send_mail.ChalklineEmail(
                            subject=f"New Message from {user['firstName']} {user['lastName']}",
                            recipients=[recipient],
                            html=message
                        )
                        msgList.append(email)
                        
                    send_mail.sendBulkMail(msgList)

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
            
        if request.form.get('deleteShift'):
            shiftId = request.form['deleteShift']
            msg = director_db.deleteShift(shiftId)
            
    shiftList = director_db.getShiftList(directorList, hidePast=hidePast)
    
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

@admin.route('/rental-data', methods=['GET', 'POST'])
def rental_data():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    if request.method == 'POST':
        
        if request.form.get('updateRental'):
            rentalName = request.form['updateRental']
            form = {}
            for key, value in request.form.items():
                if f'_{rentalName}' in key:
                    form[key.removesuffix(f"_{rentalName}")] = value
                    
            form['ageGroups'] = request.form.getlist('ageGroups_'+rentalName)
            msg = admin_db.updateRental(user, rentalName, form)
            
        elif request.form.get('removeReserve'):
            rentalName = request.form['removeReserve']
            msg = admin_db.removeReserve(user, rentalName)
            
        elif request.form.get('deleteRental'):
            rentalName = request.form['deleteRental']
            msg = admin_db.deleteRental(user, rentalName)

    rentalList = db.getRentalList(teamId='', admin=True)
    return render_template('admin/rental-data.html', user=user, msg=msg, rentalList=rentalList)

@admin.route('/add-equipment', methods=['GET', 'POST'])
def add_equipment():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    if request.method == 'POST':
        
        if request.form.get('addRental'):
            form = {
                'location': user['location'],
                'name': request.form['name'],
                'desc': request.form['desc'],
                'field': request.form['field'],
                'active': True,
                'ageGroups': request.form.getlist('ageGroups'),
                'rentalDates': []
            }
            msg = admin_db.addRental(user, form)
            if msg is None:
                return redirect(url_for('admin.rental_data'))
    return render_template('admin/add-rental.html', user=user, msg=msg)

@admin.route("/user-data", methods=['GET', 'POST'])
def user_data():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.user_data'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    userFilter = {'active': True}

    if request.method == 'POST':
        if request.form.get('updateFilter'):
            if request.form['active'] == 'undefined':
                userFilter.pop('active')
            if request.form['role'] != 'undefined':
                userFilter['role'] = request.form['role']
        
        if request.form.get('updateUser'):
            user_id = request.form['updateUser']
            priority = True if request.form[f'priority_{user_id}'] == 'True' else False
            canRemoveGame = True if request.form[f'canRemoveGame_{user_id}'] == 'True' else False
            active = True if request.form[f'active_{user_id}'] == 'True' else False
            msg = admin_db.updateUser(user, user_id, {'priority': priority, 'canRemoveGame': canRemoveGame, 'active': active})

        elif request.form.get('manageUser'):
            return redirect(url_for('view_info.user', user_id=request.form['manageUser']))

    userList = db.getUserList(criteria=userFilter, safe=True, active=False)
    return render_template("admin/user-data.html", user=user, userList=userList, userFilter=userFilter, msg=msg)