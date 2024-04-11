from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
umpire = Blueprint('umpire', __name__)

@umpire.route('/schedule', methods=['GET', 'POST'])
def schedule():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'umpire.schedule'
        return redirect(url_for('main.login'))
    elif 'umpire' not in user['role'] and 'youth' not in user['role']:
        return redirect(url_for('main.home'))

    eventFilter = get_events.EventFilter()
    msg = ''
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
            
        if request.form.get('addPlate'):
            msg = db.addPlate(user, request.form['addPlate'])
        if request.form.get('addField1'):
            msg = db.addField1(user, request.form['addField1'])
    
    userList = db.getUserList(session['location'])
    eventList = get_events.getEventList(session['location'], eventFilter, userList=userList, add_criteria={'eventType': 'Game'})
    
    sobj=srv.getSessionObj(session, msg=msg)
    return render_template('umpire/schedule.html', user=user, eventList=eventList, eventFilter=eventFilter.asdict(), sobj=sobj)

@umpire.route('/assignments', methods=['GET', 'POST'])
def assignments():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'umpire.schedule'
        return redirect(url_for('main.login'))
    elif 'umpire' not in user['role'] and 'youth' not in user['role']:
        return redirect(url_for('main.home'))
    
    eventFilter = get_events.EventFilter()
    msg = ''
    add_criteria = {'$or': [{'plateUmpire': user['userId']}, {'field1Umpire': user['userId']}]}
    
    if request.method == 'POST':
        
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
            
        if request.form.get('removeGame'):
            game = request.form['removeGame']
            msg = db.removeGame(user, game)
            
        if request.form.get('subGame'):
            game = request.form['subGame']
            return redirect(url_for('view_info.event', eventId=game, _anchor="substitute"))
            
    userList = db.getUserList(session['location'])
    eventList = get_events.getEventList(session['location'], eventFilter, add_criteria=add_criteria, userList=userList)
    
    sobj=srv.getSessionObj(session, msg=msg)
    return render_template('umpire/assignments.html', user=user, eventList=eventList, eventFilter=eventFilter.asdict(), sobj=sobj)