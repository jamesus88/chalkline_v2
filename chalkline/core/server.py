from flask import session, redirect, url_for, request
from chalkline import PROTOCOL, DOMAIN, APP_NAME, VERSION, COPYRIGHT
from chalkline.core import now
from chalkline.core.league import League

def login(user, leagueId=None, admin=None):
    if leagueId:
        league = League.get(leagueId)
        session['league'] = league

    session['user'] = user

    if admin is not None:
        session['admin'] = admin

    assert session['user'], "Login Error: 16"
    assert session['league'], "Login Error: 17"
    assert session['admin'] is not None, "Login Error: 18"

    session.permanent = True

def logout():
    session.clear()

def get_perm_group(league, user):
    if user is None or league is None:
        return {'name': None, 'perms': []}
    else:
        for g in league['perm_groups']:
            if user['permissions'][league['leagueId']] == g['name']:
                return g

def obj(context={}):
    user = session.get('user')
    league = session.get('league')
    perm_group = get_perm_group(league, user)
    res = {
        'protocol': PROTOCOL,
        'domain': DOMAIN,
        'app_name': APP_NAME,
        'version': VERSION,
        'copyright': COPYRIGHT,
        'date': now(),
        'user': user,
        'league': league,
        'user_perm_group': perm_group['name'],
        'user_perms': perm_group['perms'],
        'admin': session.get('admin'),
        'flash': session.get('flash')
    }
    res.update(context)

    return res

def authorized_only(group: str | list = None, set_next_url=None):
    user = session.get('user')
    if not user:
        if set_next_url: session['next_url'] = set_next_url
        return redirect(url_for('main.login', next=request.endpoint))
    elif group:
        league = session.get('league')
        if type(group) == list:
            if len(set(group).intersection(user['groups'][league['leagueId']])) < 1:
                raise PermissionError('This page is restricted.')
        elif group not in user['groups'][league['leagueId']]:
            raise PermissionError('This page is restricted.')
    else:
        return None

def unauthorized_only():
    if session.get('user'):
        return redirect(url_for('main.home'))