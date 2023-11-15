from flask import session
from chalkline import mail
from flask_mail import Message
import datetime
import requests

SHARE_LINK = "www.chalklinebaseball.com/"
MAIL_SENDER = 'Chalkline Baseball'
LEAGUE_CODE = "sll2024!"

def getUser():
    if 'user' in session:
        user = session['user']
    else: user = None

    return user

def logout():
    session.pop('user')
    if 'next-page' in session: session.pop('next-page')

def todaysDate(padding_hrs=0):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=-4) + datetime.timedelta(hours=padding_hrs)
    return now

def safeUser(user, session_user={}):
    user['_id'] = str(user['_id'])
    if session_user.get('userId') != user['userId']:
        if user['hidePhone']: user['phone'] = None
        if user['hideEmail']: user['email'] = None
    
    user.pop('userId')
    return user

def safeEvent(event, userList):
    default = {
        '_id': None,
        'firstName': None,
        'lastName': None,
        'fLast': None,
        'phone': None,
        'email': None,
        'teams': None
    }
    
    event['plateUmpireInfo'] = default.copy()
    event['field1UmpireInfo'] = default.copy()
    event['fieldRequestInfo'] = default.copy()
    
    for user in userList:
        if event['plateUmpire'] == user['userId']:
            event['plateUmpireInfo']['_id'] = str(user['_id'])
            event['plateUmpireInfo']['firstName'] = user['firstName']
            event['plateUmpireInfo']['lastName'] = user['lastName']
            event['plateUmpireInfo']['fLast'] = user['firstName'][0] + '. ' + user['lastName']
            event['plateUmpireInfo']['phone'] = user['phone']
            event['plateUmpireInfo']['email'] = user['email']
            event['plateUmpireInfo']['teams'] = user['teams']
            
        if event['field1Umpire'] == user['userId']:
            event['field1UmpireInfo']['_id'] = str(user['_id'])
            event['field1UmpireInfo']['firstName'] = user['firstName']
            event['field1UmpireInfo']['lastName'] = user['lastName']
            event['field1UmpireInfo']['fLast'] = user['firstName'][0] + '. ' + user['lastName']
            event['field1UmpireInfo']['phone'] = user['phone']
            event['field1UmpireInfo']['email'] = user['email']
            event['field1UmpireInfo']['teams'] = user['teams']
            
        if event['fieldRequest'] == user['userId']:
            event['fieldRequestInfo']['_id'] = str(user['_id'])
            event['fieldRequestInfo']['firstName'] = user['firstName']
            event['fieldRequestInfo']['lastName'] = user['lastName']
            event['fieldRequestInfo']['fLast'] = user['firstName'][0] + '. ' + user['lastName']
            event['fieldRequestInfo']['phone'] = user['phone']
            event['fieldRequestInfo']['email'] = user['email']
            event['fieldRequestInfo']['teams'] = user['teams']
        
    event.pop('plateUmpire')
    event.pop('field1Umpire')
    event.pop('fieldRequest')
    
    event['_id'] = str(event['_id'])
    
    return event

def sendMail(subject: str = 'Message from Chalkline Baseball', body: str = 'www.chalklinebaseball.com', sender: str = MAIL_SENDER, recipients: list = []):
    msg = Message(
        subject=subject,
        body=body,
        sender=sender,
        bcc=recipients
    )
    #mail.send(msg)
    print(f'Message sent to {str(msg.bcc)}')

def createEmailList(users):
    return [user['email'] for user in users if user['emailNotifications']]

def createPhoneList(users):
    return [user['phone'] + '@' + user['sms-gateway'] for user in users if user['phoneNotifications']]

