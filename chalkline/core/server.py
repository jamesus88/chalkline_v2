from flask import session, redirect, url_for, request
from chalkline import PROTOCOL, DOMAIN, APP_NAME, VERSION, COPYRIGHT

def login(user, league=None):
    if not league:
        league = session.get('league')
    
    if not (league and user):
        raise RuntimeError('User and League must be present for login!')
    
    if league not in user['leagues']:
        raise TypeError('You are not a member of this league.')
    
    else:
        session['user'] = user
        session['league'] = league

def logout():
    session.clear()

def obj(context={}):
    res = {
        'protocol': PROTOCOL,
        'domain': DOMAIN,
        'app_name': APP_NAME,
        'version': VERSION,
        'copyright': COPYRIGHT,
        'user': session.get('user'),
        'league': session.get('league')
    }
    res.update(context)

    return res

def lock_blueprint():
    authorized_only()
    if request.blueprint:
        if request.blueprint not in session['user']['groups']:
            raise PermissionError('You are not authorized to be here!')

def authorized_only():
    if not session.get('user'):
        return redirect(url_for('main.login', next=request.endpoint))

def unauthorized_only():
    if session.get('user'):
        return redirect(url_for('main.home'))