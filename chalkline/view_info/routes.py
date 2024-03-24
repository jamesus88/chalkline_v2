from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db
from chalkline.admin import admin_db
from chalkline import server as srv
view_info = Blueprint('view_info', __name__)

@view_info.route("/event/<eventId>", methods=['GET', 'POST'])
def event(eventId):
    user = srv.getUser()
    if user is None:
        session['next-url'] = request.path
        return redirect(url_for('main.login'))
    
    msg = ''
    smsg = None
    userList = db.getUserList(session['location'])
    teamsList = db.getTeams(session['location'])
    
    if request.method == 'POST':
        this_event = db.getEventInfo(eventId)
        if request.form.get('updateEvent'):
            msg = db.updateEvent(session['location'], user, this_event, request.form, userList, editRules=True, editContacts=True)
            
        elif request.form.get('subGame'):
            sub = db.getUser(request.form['sub'])
            smsg = db.substituteUmpire(user, this_event, sub)
    
    event = db.getEventInfo(eventId)
    
    if not event:
        return redirect(url_for('league.master_schedule'))
    else:
        event = srv.safeEvent(event, userList)
        
    userList = [srv.safeUser(x) for x in userList]
    
    sobj=srv.getSessionObj(session, msg=msg, smsg=smsg)
    return render_template("view_info/event.html", user=user, event=event, teamsList=teamsList, userList=userList, sobj=sobj)

@view_info.route("/user/<user_id>", methods=['GET', 'POST'])
def user(user_id=None):
    user = srv.getUser()
    if user is None:
        session['next-url'] = request.path
        return redirect(url_for('main.login'))
    elif user_id is None:
        return redirect(url_for('main.home'))
    
    view_user = srv.safeUser(db.getUser(_id=user_id))
    msg = ''

    if request.method == 'POST':
        if 'admin' not in user['role']:
            raise PermissionError('Error: admin credentials required.')

        if request.form.get('permissionSet'):
            ps = request.form['permissionSet']
            view_user['permissionSet'] = ps
            msg = admin_db.updateUser(user, user_id, {'permissionSet': ps})

        elif request.form.get('addRole'):
            role = request.form['addRole']
            if role in view_user['role']:
                msg = 'Error: user already has that role.'
            else:
                user_roles = view_user['role']
                user_roles.append(role)
                view_user['role'] = user_roles
                msg = admin_db.updateUser(user, user_id, {'role': user_roles})

        elif request.form.get('removeRole'):
            role = request.form['removeRole']
            if role not in view_user['role']:
                msg = 'Error: user does not have that role.'
            else:
                user_roles = view_user['role']
                user_roles.remove(role)
                view_user['role'] = user_roles
                msg = admin_db.updateUser(user, user_id, {'role': user_roles})

        elif request.form.get('removeLoc'):
            user_leagues = view_user['locations']
            user_leagues.remove(session['location'])
            view_user['locations'] = user_leagues
            msg = admin_db.updateUser(user, user_id, {'locations': user_leagues})

    sobj=srv.getSessionObj(session, msg=msg)
    return render_template("view_info/user.html", user=user, view_user=view_user, sobj=sobj)