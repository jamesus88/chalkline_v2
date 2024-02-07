from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
teams = Blueprint('teams', __name__)


@teams.route('/schedule', methods=['GET', 'POST'])
def schedule():
    user = srv.getUser()
    if user is None:
        return redirect(url_for('main.login'))
    elif 'coach' not in user['role'] and 'parent' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    eventFilter = get_events.EventFilter()
    if len(user['teams']) > 0:
        eventFilter.teamId = user['teams'][0]
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
            
        if request.form.get('requestField1Umpire'):
            gameId = request.form['requestField1Umpire']
            msg = db.requestField1Umpire(user, gameId)
            
        if request.form.get('removeRequest'):
            gameId = request.form['removeRequest']
            msg = db.removeRequest(user, gameId)
            
            
    userList = db.getUserList()
    eventList = get_events.getEventList(eventFilter, userList=userList)
    
    return render_template('teams/schedule.html', user=srv.safeUser(user), eventList=eventList, eventFilter=eventFilter.asdict(), msg=msg)

@teams.route("/info", methods=['GET', 'POST'])
def info():
    user = srv.getUser()
    if user is None:
        return redirect(url_for('main.login'))
    elif 'coach' not in user['role'] and 'parent' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    teamId = None
    if len(user['teams']) > 0:
        teamId = user['teams'][0]
    else:
        return redirect(url_for('main.profile'))
    
    
    if request.method == 'POST':
        teamId = request.form.get('teamId')
    
    team = db.getTeams({'teamId': teamId})[0]
    teamContacts = [srv.safeUser(contact, user) for contact in db.getUserList({'teams': teamId})]
    link = srv.SHARE_LINK + f"invite/add-team/{teamId}"
    
    return render_template("teams/info.html", user=user, team=team, msg=msg, teamContacts=teamContacts, link=link)
    
@teams.route("/rentals", methods=['GET', 'POST'])
def rentals():
    user = srv.getUser()
    if user is None:
        return redirect(url_for('main.login'))
    elif 'coach' not in user['role'] and 'parent' not in user['role']:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    eventFilter = get_events.EventFilter()
    eventFilter.eventTypeFilter = 'Practice'
    if len(user['teams']) > 0:
        eventFilter.teamId = user['teams'][0]
    elif len(user['teams']) < 1:
        return redirect(url_for('main.profile'))
        
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
            
        if request.form.get('rentEquipment'):
            eventId, rentalName = request.form['rentEquipment'].split(sep='_')
            msg = db.rentEquipment(user, eventId, rentalName)
            
        if request.form.get('returnRental'):
            eventId, rentalName = request.form['rentEquipment'].split(sep='_')
            msg = db.returnRental(user, eventId)
            
    
    userList = db.getUserList()
    eventList = get_events.getEventList(eventFilter, userList=userList)
    rentalList = db.getRentalList(eventFilter.teamId)
    return render_template("teams/rentals.html", user=user, eventList=eventList, rentalList=rentalList, eventFilter=eventFilter.asdict(), msg=msg)
    