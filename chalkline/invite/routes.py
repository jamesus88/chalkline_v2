from flask import redirect, url_for, session, Blueprint, render_template, request
from chalkline import db, get_events
from chalkline import server as srv
from chalkline import send_mail
from werkzeug.security import generate_password_hash
import os
invite = Blueprint('invite', __name__)

@invite.route('/add-team/<teamId>')
def add_team(teamId=None):
    if not teamId:
        return redirect(url_for('main.home'))
    user = srv.getUser()
    if user is None:
        session['next-url'] = request.path
        return redirect(url_for('main.login'))
    if 'coach' in user['role'] or 'parent' in user['role']:
        response = db.addTeamToUser(user, teamId)
        if type(response) != str:
            user = response
            session['user'] = user
        
    return redirect(url_for('main.profile'))

@invite.route("/reset/<email>/<token>", methods=['GET', 'POST'])
def password_reset(email=None, token=None):
    if email is None or token is None:
        return redirect(url_for('main.home'))
    
    user = db.userData.find_one({'email': email})
    if user is None:
        return redirect(url_for('main.home'))
    elif 'reset_token' not in user:
        return redirect(url_for('main.home'))
    elif token != user['reset_token']:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    if request.method == 'POST':
        pword = generate_password_hash(request.form['pword'])
        db.userData.update_one({'email': email}, {'$set': {'pword': pword}, '$unset': {'reset_token': ''}})
        msg = "Your password has been updated."
    
    return render_template("main/reset-password.html", email=user['email'], msg=msg, user=None)
    
@invite.route('/daily-reminders', methods=['GET', 'POST'])
def daily_reminders():
    print('Daily Reminder Job Attempted...')
    
    if request.args.get('chalkline_auth') == os.environ.get('CHALKLINE_AUTH') and request.method == 'POST':
        today = srv.todaysDate
        nextWeek = today(17 + 24*6) # rest of today (7:00) + 6 days
        eventFilter = get_events.EventFilter()
        eventList = get_events.getEventList(eventFilter, {'eventDate': {'$gte': today(), '$lte': nextWeek}}, safe=False)
        
        day = srv.todaysDate().weekday() # [0, 1, ... , 6]
        userList = db.getUserList()
        
        usersToMail = userList[day::7]
        
        msg, code = srv.sendReminders(eventList, usersToMail)
        
        print('Daily Reminder Job executed.')
        return msg, code
    else:
        raise PermissionError('PermissionError: Resource is Forbidden.')

@invite.route('/sub-request')
@invite.route('/sub-request/<eventId>')
@invite.route('/sub-request/<eventId>/<code>')
@invite.route('/sub-request/<eventId>/<code>/<pos>', methods=['POST', 'GET'])
def sub_request(eventId: None|str=None, code: None|str=None, pos: None|str = None):
    user = srv.getUser()
    if user is None:
        session['next-url'] = request.path
        return redirect(url_for('main.login'))
    elif 'umpire' not in user['role'] and 'youth' not in user['role']:
        raise PermissionError("Error: You are not authorized to umpire games")
    
    if not(eventId and code and pos):
        raise Exception("Pre-condition failure: missing url parameters")
    
    event = db.getEventInfo(eventId)
    if not event:
        raise Exception("Event does not exist.")
    
    if event['eventDate'] < srv.todaysDate():
        raise Exception("Error: cannot edit past events.")
    
    if not code.isdigit() or not pos.isdigit():
        raise Exception("Error: invalid parameters.")

    if 'sub-code' not in event:
        raise Exception("Error: substitution request is no longer valid.")
    
    if int(code) != event['sub-code']:
        raise PermissionError("Error: invalid sub-code")
    
    if pos == '0':
        pos = ('Plate Umpire', 0)
    elif pos == '1':
        pos = ('Field Umpire', 1)
    else:
        raise Exception("Error: invalid position")
    
    msg = ''
    
    if request.method == 'POST':
        if request.form.get('accept'):
                if pos[1] == 0:
                    old_umpire = db.getUser(userId=event['plateUmpire'])
                    msg = db.addPlate(user, eventId, check_empty=False)
                else:
                    old_umpire = db.getUser(userId=event['field1Umpire'])
                    msg = db.addField1(user, eventId, check_empty=False)
                    
                if 'Error:' not in msg:
                    print(f"Sub: {user['userId']} for {pos[0]} in {eventId}")
                    db.removeSubCode(eventId)
                    email = send_mail.ChalklineEmail(
                        subject="Substitution Request Accepted!",
                        recipients=['aidan.hurwitz88@gmail.com'],
                        html=render_template("emails/shift-fulfilled.html", event=event, team=pos[0])
                    )
                    send_mail.sendMail(email)
                    return redirect(url_for('umpire.assignments'))
        
        elif request.form.get('decline'):
            db.removeSubCode(eventId)
            return redirect(url_for('main.home'))
            
            
    # correct code and event
    userList = db.getUserList()
    return render_template("umpire/substitute.html", user=user, event=srv.safeEvent(event, userList), pos=pos, msg=msg)
    
    
    
    
    