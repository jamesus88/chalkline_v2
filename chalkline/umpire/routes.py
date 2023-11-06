from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
umpire = Blueprint('umpire', __name__)

@umpire.route('/')
def home():
    return "umpire home"

@umpire.route('/schedule', methods=['GET', 'POST'])
def schedule():
    user = srv.getUser()
    
    eventFilter = get_events.EventFilter()
    msg = ''
    
    if request.method == 'POST':
        print(request.form.keys())
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
            
        if request.form.get('addPlate'):
            print('add plate')
            msg = db.addPlate(user, request.form['addPlate'])
        if request.form.get('addField1'):
            print('add field1')
            msg = db.addField1(user, request.form['addField1'])
    
    userList = db.getUserList()
    eventList = get_events.getEventList(eventFilter, userList=userList)
    
    
    return render_template('umpire/schedule.html', user=srv.safeUser(user), eventList=eventList, eventFilter=eventFilter.asdict(), msg=msg)

@umpire.route('/assignments', methods=['GET', 'POST'])
def assignments():
    user = srv.getUser()
    
    eventFilter = get_events.EventFilter()
    msg = ''
    add_criteria = {'$or': [{'plateUmpire': user['userId']}, {'field1Umpire': user['userId']}]}
    
    if request.method == 'POST':
        
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
            
        if request.form.get('removeGame'):
            game = request.form['removeGame']
            msg = db.removeGame(user, game)
            
    userList = db.getUserList()
    eventList = get_events.getEventList(eventFilter, add_criteria=add_criteria, userList=userList)
    
    return render_template('umpire/assignments.html', user=srv.safeUser(user), eventList=eventList, eventFilter=eventFilter.asdict(), msg=msg)