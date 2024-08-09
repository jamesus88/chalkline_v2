from flask import session, redirect, url_for, request
from chalkline import PROTOCOL, DOMAIN, APP_NAME, VERSION, COPYRIGHT

def login(user, league=None, admin=None):
    if not league:
        league = session.get('league')
    if admin is None:
        admin = session.get('admin', False)
    
    if not (league and user):
        raise RuntimeError('User and League must be present for login!')
    
    if league not in user['leagues']:
        raise TypeError('You are not a member of this league.')
    
    session['user'] = user
    session['league'] = league
    session['admin'] = admin

    session.permanent = True

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
        'league': session.get('league'),
        'admin': session.get('admin'),
        'flash': session.get('flash')
    }
    res.update(context)

    return res

def authorized_only(group: str | list = None):
    user = session.get('user')
    if not user:
        return redirect(url_for('main.login', next=request.endpoint))
    elif group:
        if type(group) == list:
            if len(set(group).intersection(user['groups'])) < 1:
                raise PermissionError('This page is restricted.')
        elif group not in user['groups']:
            raise PermissionError('This page is restricted.')
    else:
        return None

def unauthorized_only():
    if session.get('user'):
        return redirect(url_for('main.home'))