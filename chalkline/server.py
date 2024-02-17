from flask import session, render_template
import datetime, time
import chalkline.send_mail as send_mail

SHARE_LINK = "https://chalklinebaseball.com/"
LEAGUE_CODE = "sll2024!"
        
def getUser():
    if 'user' in session:
        user = session['user']
    else: user = None

    return user

def logout():
    session.pop('user')
    if 'next-page' in session: session.pop('next-page')
    if 'next-url' in session: session.pop('next-url')

def todaysDate(padding_hrs=0):
    '''
    #### padding_hrs: int x -> adds x hrs to EST
    ex: todaysDate(2) = right now + 2 hours into the future.
    '''
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=-5) + datetime.timedelta(hours=padding_hrs)
    return now

def safeUser(user, session_user={}):
    user['_id'] = str(user['_id'])
    user['fLast'] = user['firstName'][0] + '. ' + user['lastName']
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

def createEmailList(users):
    return [user['email'] for user in users if user['emailNotifications']]

def createPhoneList(users):
    return [user['phone'] + '@' + user['sms-gateway'] for user in users if user['phoneNotifications']]

def alertUsersOfEvent(old, new, userList):
    print('Alerting users of event changes...')
    users = []
    
    for user in userList:
        if user['userId'] == old['plateUmpire']: users.append(user)
        elif user['userId'] == old['field1Umpire']: users.append(user)
        elif user['userId'] == old['fieldRequest']: users.append(user)
        elif old['awayTeam'] in user['teams']: users.append(user)
        elif old['homeTeam'] in user['teams']: users.append(user)
        
    emailList = createEmailList(users)
    
    msgList = []
                
    for email in emailList:
        msg = send_mail.ChalklineEmail(
            subject=f"New changes: {new['eventAgeGroup']} {new['eventDate'].strftime('%a %m/%d @ %H:%M')}",
            recipients=[email],
            html=render_template("emails/event-update.html", old=old, new=new)
        )
        msgList.append(msg)
        
    send_mail.sendBulkMail(msgList)

    return True

def sendReminders(eventList, userList, shiftList = None):
    # {
    #     'data': [{event: data, role: str}]
    # }
    data = {}
    
    for event in eventList:
        for user in userList:
            userId = user['userId']
            role = None
            if event['plateUmpire'] == userId:
                role = 'Plate Umpire'
            elif event['field1Umpire'] == userId:
                role = 'Field Umpire'
            elif event['homeTeam'] in user['teams']:
                role = 'Home Team'
            elif event['awayTeam'] in user['teams']:
                role = 'Away Team'
            elif event['umpireDuty'] in user['teams'] and event['field1Umpire'] is None:
                role = 'Umpire Duty'
        
            if role is not None and user['emailNotifications']:
                if user['email'] not in data:
                    data[user['email']] = {'user': user, 'events': [{'event': event, 'role': role}]}
                else:
                    data[user['email']]['events'].append({'event': event, 'role': role})
                    
    mailList = []
    for email, events in data.items():
        
        mail = send_mail.ChalklineEmail(
            subject='Reminder: You have events today!',
            recipients=[email],
            html=render_template("emails/reminder.html", user=events['user'], events=events['events'])
        )
        mailList.append(mail)
        
    print(f'Sending {len(mailList)} daily reminders...')
    
    send_mail.sendBulkMail(mailList, asynchronous=False)
    
    return "Successfully sent daily reminders", 200
        
    