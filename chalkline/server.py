from flask import session
import datetime

def getUser():
    if 'user' in session:
        user = session['user']
    else: user = None

    return user

def logout():
    session.pop('user')

def todaysDate():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=-4)
    return now
    