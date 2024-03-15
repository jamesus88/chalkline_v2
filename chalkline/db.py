import pymongo, bson, datetime, os, uuid, re
import chalkline.server as server
import chalkline.send_mail as send_mail
from flask import render_template
from random import randint
from werkzeug.security import generate_password_hash, check_password_hash
import certifi

client = pymongo.MongoClient(os.environ.get('PYMONGO_CLIENT'), connect=False,  tlsCAFile=certifi.where())
db = client['chalkline']

eventData = db['eventData']
userData = db['userData']
permissions = db['permissions']
reportData = db['reportData']
teamData = db['teamData']
playerData = db['playerData']
leagueData = db['leagueData']
venueData = db['venueData']
directorData = db['directorData']
rentalData = db['rentalData']

def authenticate(email, pword):
    user = userData.find_one_and_update({'email': email}, {'$set': {'last_attempt': server.todaysDate()}}, return_document=pymongo.ReturnDocument.AFTER)
    if user:
        print(f"Attempted Login: {email}")
        correct = check_password_hash(user['pword'], pword)
        print(f"Password Authenticated: {correct}")
        if correct:
            user['_id'] = str(user['_id'])
            user = appendPermissions(user)
            print(f"Successful Login: {email}")
            return user
        else:
            print(f"Failed Login: {email}")
    
    return None

def verifyEmail(email):
    if userData.find_one({'email': email}):
        return True
    else: return False
    
def appendPermissions(user):
    permissionSet = permissions.find_one({'set': user['permissionSet']})
    permissionSet.pop('_id')
    user['permissions'] = permissionSet
    
    return user

def getUserList(criteria={}, safe=False, active=True):
    if active: criteria['active'] = True
    if safe:
        return [server.safeUser(user) for user in userData.find(criteria).sort('lastName', pymongo.ASCENDING)]
    
    return list(userData.find(criteria).sort('lastName', pymongo.ASCENDING))

def getUser(_id=None, email=None, userId=None):
    user = userData.find_one({'$or': [{'_id': bson.ObjectId(_id)}, {'email': email}, {'userId': userId}]})
    user = appendPermissions(user)
    return user

def checkDuplicateUser(newUser):
    user = userData.find_one({"$or": [{'userId': newUser['userId']}, {'email': newUser['email']}, {'phone': newUser['phone']}]})
    if user: return True
    else: return False
    
def createUser(form):
    response = {
        'newUser': {
          "location": form['location'],
          "firstName": form['firstName'].title().strip(),
          "lastName": form['lastName'].title().strip(),
          "userId": form['email'].strip().lower(),
          "email": form['email'].strip().lower(),
          "phone": form['phone'],
          "sms-gateway": form.get('carrier'),
          "pword": generate_password_hash(form['pword']),
          "role": [],
          "teams": [],
          "permissionSet": "C0",
          "canRemoveGame": False,
          "emailNotifications": True,
          "phoneNotifications": True,
          "hideEmail": False,
          "hidePhone": False,
          "priority": False
        },
        'error': None
    }
    tel = form['phone']
    tel = tel.removeprefix("+")
    tel = tel.removeprefix("1")     # remove leading +1 or 1
    tel = re.sub("[ ()-]", '', tel) # remove space, (), -

    try: tel = f"{tel[:3]}-{tel[3:6]}-{tel[6:]}"
    except: response['error'] = "Invalid phone number."
    
    response['newUser']['phone'] = tel

    
    if form.get('role-coach'):
        response['newUser']['role'].append('coach')
    if form.get('role-parent'):
        response['newUser']['role'].append('parent')
    if form.get('role-umpire'):
        response['newUser']['role'].append('umpire')
        response['newUser']['permissionSet'] = "U0"
        if form['role-pass'] != server.LEAGUE_CODE:
            response['error'] = "Incorrect league code. Umpires must enter a valid league code to create an account."
    if form.get('role-youth'):
        response['newUser']['role'].append('youth')
        response['newUser']['permissionSet'] = "Y0"
    if form.get('role-board'):
        response['newUser']['role'].append('board')
        if form['role-pass'] != server.LEAGUE_CODE:
            response['error'] = "Incorrect league code. Board Members must enter a valid league code to create an account."
        
    if len(response['newUser']['role']) < 1:
        response['error'] = 'Select at least one account role'
        
    if checkDuplicateUser(response['newUser']):
        response['error'] = 'User ID, email, or phone number already exists. Try logging in...'

    return response

def saveUser(user):
    userData.insert_one(user)
    user['_id'] = str(user['_id'])
    user = appendPermissions(user)
    return user

def updateProfile(userId, form):
    writable = {
        'firstName': form['firstName'],
        'lastName': form['lastName'],
        'email': form['email'],
        'phone': form['phone'],
        'emailNotifications': False,
        'phoneNotifications': False,
        "hideEmail": False,
        "hidePhone": False
    }
    
    if form.get('emailNotifications'):
        writable['emailNotifications'] = True
    if form.get('phoneNotifications'):
        writable['phoneNotifications'] = True
    if form.get('hideEmail'):
        writable['hideEmail'] = True
    if form.get('hidePhone'):
        writable['hidePhone'] = True
        
    user = userData.find_one_and_update({'userId': userId}, {'$set': writable}, return_document=pymongo.ReturnDocument.AFTER)
    user['_id'] = str(user['_id'])
    
    user = appendPermissions(user)
    
    return user

def getTeamsFromUser(teamCodes):
    teams = teamData.find({"teamId": {"$in": teamCodes}})
    teamsList = []
    
    for team in teams:
        team['_id'] = str(team['_id'])
        teamsList.append(team)
    
    return teamsList

def getTeams(criteria={}):
    teams = teamData.find(criteria)

    teamsList = []
        
    for team in teams:
        team['_id'] = str(team['_id'])
        teamsList.append(team)
    teamsList = sorted(teamsList, key=lambda x: x['teamId'])    
    return teamsList
        
def removeTeamFromUser(user, teamCode):
    user['teams'].remove(teamCode)
    user = userData.find_one_and_update({"userId": user['userId']}, {"$set": {"teams": user['teams']}}, return_document=pymongo.ReturnDocument.AFTER)
    user['_id'] = str(user['_id'])
    
    user = appendPermissions(user)
    return user

def addTeamToUser(user, teamCode):
    if teamCode in user['teams']:
        return "Error - team already added."
    elif not teamData.find_one({"teamId": teamCode}):
        return "Error - team code does not exist."
    
    user['teams'].append(teamCode)
    user = userData.find_one_and_update({"userId": user['userId']}, {"$set": {"teams": user['teams']}}, return_document=pymongo.ReturnDocument.AFTER)
    user['_id'] = str(user['_id'])
    
    user = appendPermissions(user)
    return user

def addPlate(user, gameId, check_empty=True, check_conflicts=True):
    criteria = [{'_id': bson.ObjectId(gameId)}, {'eventAgeGroup': {'$nin': user['permissions']['prohibitedPlate']}}]
    if check_empty: criteria.append({'plateUmpire': None})
    
    game = eventData.find_one({'$and': criteria})
    
    if game:
        if check_conflicts:
            conflicts = getConflicts(user, game)
            if conflicts:
                return f"Error: you are already registered for an event at this date and time (Field {conflicts[0]['eventField']})."

        eventData.update_one({'_id': game['_id']}, {'$set': {'plateUmpire': user['userId']}})
        msg = f'Successfully added {user["firstName"][0]}. {user["lastName"]} for plate duty.'
        print(f"Plate added: {user['userId']} for {gameId}")
        if game['fieldRequest'] and game['umpireDuty'] and not game['editRules']['hasField1Umpire']:
            coach = userData.find_one({'userId': game['fieldRequest']})
            
            if coach['emailNotifications']:
                email = send_mail.ChalklineEmail(
                    subject="Umpire Shift Covered!",
                    recipients=[coach['email']],
                    html=render_template("emails/shift-fulfilled.html", team=game['umpireDuty'], event=game)
                )
                send_mail.sendMail(email)
    else:
        msg = 'Error: position filled or unavailable'
        
    return msg

def addField1(user, gameId, check_empty=True, check_conflicts=True):
    criteria = [{'_id': bson.ObjectId(gameId)}, {'eventAgeGroup': {'$nin': user['permissions']['prohibitedField']}}]
    if check_empty: criteria.append({'field1Umpire': None})
    
    game = eventData.find_one({'$and': criteria})
    
    if game:
        if check_conflicts:
            if getConflicts(user, game):
                return 'Error: you are already registered for an event at this date and time.'
        
        eventData.update_one({'_id': game['_id']}, {'$set': {'field1Umpire': user['userId']}})
        msg = f'Successfully added {user["firstName"][0]}. {user["lastName"]} for field duty.'
        print(f"Field1 added: {user['userId']} for {gameId}")
        if game['fieldRequest'] and game['umpireDuty']:
            coach = userData.find_one({'userId': game['fieldRequest']})
            
            if coach['emailNotifications']:
                email = send_mail.ChalklineEmail(
                    subject="Umpire Shift Covered!",
                    recipients=[coach['email']],
                    html=render_template("emails/shift-fulfilled.html", team=game['umpireDuty'], event=game)
                )
                send_mail.sendMail(email)
    else:
        msg = 'Error: position filled or unavailable'
        
    return msg

def removeGame(user, gameId):
    game = eventData.find_one({'_id': bson.ObjectId(gameId)})
    setData = {}
    if game['editRules']['removable'] or user['canRemoveGame']:
        if user['userId'] == game['plateUmpire']:
            setData['plateUmpire'] = None
        if user['userId'] == game['field1Umpire']:
            setData['field1Umpire'] = None
            
        eventData.update_one({'_id': bson.ObjectId(gameId)}, {'$set': setData})

        msg = 'Successfully removed 1 game.'

    else:
        msg = "Error: you do not have permission to remove this game. Contact administrator."
        
    return msg

def requestField1Umpire(user, gameId):
    game = eventData.find_one({'_id': bson.ObjectId(gameId)})
    
    if game['editRules']['fieldRequestAddable'] and 'coach' in user['role'] and game['fieldRequest'] is None:
        eventData.update_one({'_id': bson.ObjectId(gameId)}, {'$set': {'fieldRequest': user['userId']}})
        msg = 'Successfully requested youth umpire.'
        print(f"Youth Umpire Requested: {gameId} by {user['userId']}")
    
    else:
        msg = 'Error: you do not have permission to request a field umpire for this game.'
        
    return msg

def removeRequest(user, gameId):
    game = eventData.find_one({'_id': bson.ObjectId(gameId)})
    msg = ''
    
    if 'coach' not in user['role']:
        msg = 'Error: You do not have permission to remove this umpire request.'
        
    if game['field1Umpire'] is not None:
        msg = 'Error: Umpire Request already fulfilled.'
    else:
        eventData.update_one({'_id': bson.ObjectId(gameId)}, {'$set': {'fieldRequest': None}})
        msg = 'Successfully removed request.'
    
    return msg

def getConflicts(user, event):
    criteria = []
    criteria.append({'$or': [{'plateUmpire': user['userId']}, {'field1Umpire': user['userId']}]})
    criteria.append({'eventDate': {'$gte': event['eventDate'], '$lte': event['eventDate'] + datetime.timedelta(hours=1.5)}})
    subConflict = list(eventData.find({'$and': criteria}))
    
    if len(subConflict) < 1:
        return None
    else:
        return subConflict
    
def substituteUmpire(user, event, sub):
    isPlate, isField = False, False
    if user['userId'] == event['plateUmpire']: isPlate = True
    if user['userId'] == event['field1Umpire']: isField = True
    
    if isPlate:
        if event['eventAgeGroup'] in sub['permissions']['prohibitedPlate']:
            return "Error: selected umpire is not cleared for this level"
    elif isField:
        if event['eventAgeGroup'] in sub['permissions']['prohibitedField']:
            return "Error: selected umpire is not cleared for this level"
    else:
        return "Error: you are no longer signed up for this event."
    
    if event['eventDate'] < server.todaysDate():
        return "Error: cannot edit past events."
    
    if 'sub-code' in event:
        return "Error: this event has an open request already. Contact an administrator."
    
    if getConflicts(sub, event):
        return "Error: substitute umpire is already registered for a game at this time."
    
    pos = ('Plate Umpire', 0) if isPlate else ('Field Umpire', 1)
    code = randint(0, 99999999) * 10 + pos[1]
    
    eventData.update_one({'_id': event['_id']}, {'$set': {'sub-code': code}})
    
    msg = send_mail.ChalklineEmail(
        subject=f"New Substitute Request from {user['firstName'][0]}. {user['lastName']}",
        recipients=[sub['email']],
        html=render_template('emails/substitute-req.html', user=user, event=event, code=code, pos=pos)
    )
    send_mail.sendMail(msg)

    print(f"Sub Request: {pos[0]} {sub['userId']} for {user['userId']} ({str(event['_id'])})")
    
    return f"Successfully requested {sub['firstName'][0]}. {sub['lastName']} to sub-in as {pos[0]}!"
    
def removeSubCode(eventId):
    eventData.update_one({'_id': bson.ObjectId(eventId)}, {'$unset': {'sub-code': 1}})
    return True
    
def getEventInfo(eventId, add_criteria={}):
    add_criteria['_id'] = bson.ObjectId(eventId)
    return eventData.find_one(add_criteria)

def updateEvent(_user, event, form, userList, editRules=False, editContacts=False, ignoreDate=False):
    if 'admin' not in _user['role']:
        return "Error: You do not have permission to edit events."
    
    if event['eventDate'] < server.todaysDate(padding_hrs=-2) and not ignoreDate:
        return "Error: cannot edit past events."
    
    writable = {}

    if editContacts:
        writable['plateUmpire'] = None
        writable['field1Umpire'] = None
        writable['fieldRequest'] = None
        for user in userList:
            if str(user['_id']) == form.get('plateUmpire'):
                writable['plateUmpire'] = user['userId']
            if str(user['_id']) == form.get('field1Umpire'):
                writable['field1Umpire'] = user['userId']
            if str(user['_id']) == form.get('fieldRequest'):
                writable['fieldRequest'] = user['userId']
    
    if form.get('eventDate'): writable['eventDate'] = datetime.datetime.strptime(form['eventDate'], "%Y-%m-%dT%H:%M")
    if form.get('eventVenue'): writable['eventVenue'] = form['eventVenue']
    if form.get('eventAgeGroup'): writable['eventAgeGroup'] = form['eventAgeGroup']
    if form.get('awayTeam'): writable['awayTeam'] = form['awayTeam']
    if form.get('homeTeam'): writable['homeTeam'] = form['homeTeam']
    if form.get('eventType'): writable['eventType'] = form['eventType']
    if form.get('eventField'): writable['eventField'] = form['eventField']
    if form.get('status'): writable['status'] = form['status']
    if form.get('umpireDuty'): writable['umpireDuty'] = form['umpireDuty']
    
    if editRules:
        writable['editRules'] = {}
        if form.get('visible'): writable['editRules']['visible'] = True
        else: writable['editRules']['visible'] = False
        if form.get('hasPlateUmpire'): writable['editRules']['hasPlateUmpire'] = True
        else: writable['editRules']['hasPlateUmpire'] = False
        if form.get('plateUmpireAddable'): writable['editRules']['plateUmpireAddable'] = True
        else: writable['editRules']['plateUmpireAddable'] = False
        if form.get('hasField1Umpire'): writable['editRules']['hasField1Umpire'] = True
        else: writable['editRules']['hasField1Umpire'] = False
        if form.get('field1UmpireAddable'): writable['editRules']['field1UmpireAddable'] = True
        else: writable['editRules']['field1UmpireAddable'] = False
        if form.get('hasFieldRequest'): writable['editRules']['hasFieldRequest'] = True
        else: writable['editRules']['hasFieldRequest'] = False
        if form.get('fieldRequestAddable'): writable['editRules']['fieldRequestAddable'] = True
        else: writable['editRules']['fieldRequestAddable'] = False
        if form.get('removable'): writable['editRules']['removable'] = True
        else: writable['editRules']['removable'] = False
    
    old_game = eventData.find_one_and_update({'_id': bson.ObjectId(event['_id'])}, {'$set': writable})
    new_game = eventData.find_one({'_id': bson.ObjectId(event['_id'])})
    
    different_keys = []
    for key in old_game:
        if old_game[key] != new_game[key]:
            different_keys.append(key)
            
    if any(key in different_keys for key in ['eventDate', 'eventVenue', 'eventField', 'status']):
        server.alertUsersOfEvent(old_game, new_game, getUserList())
            
    print(f"Event updated: {event['_id']} by {_user['userId']}")
    return 'Successfully updated event.'

def deleteEvent(user, eventId, ignoreDate=False):
    criteria = {'_id': bson.ObjectId(eventId)}
    event = eventData.find_one(criteria)
    if (event['eventDate'] > server.todaysDate() or ignoreDate) and 'admin' in user['role']:
        eventData.delete_one(criteria)
        print(f"Event Deleted: {eventId} by {user['userId']}")
        return "Successfully deleted game"
    else:
        return "Error: cannot edit past events"
    
def addEvent(user, form):
    writable = {
        'eventType': form['eventType'],
        'eventLocation': user['location'],
        'eventVenue': form['eventVenue'],
        'eventDate': datetime.datetime.strptime(form['eventDate'], "%Y-%m-%dT%H:%M"),
        'eventAgeGroup': form['eventAgeGroup'],
        'eventField': form['eventField'],
        'awayTeam': form['awayTeam'],
        'homeTeam': form['homeTeam'],
        'umpireDuty': form['umpireDuty'],
        'status': form['status'],
        'plateUmpire': None,
        'field1Umpire': None,
        'fieldRequest': None,
        'editRules': {} 
    }
    
    if form.get('visible'): writable['editRules']['visible'] = True
    else: writable['editRules']['visible'] = False
    if form.get('hasPlateUmpire'): writable['editRules']['hasPlateUmpire'] = True
    else: writable['editRules']['hasPlateUmpire'] = False
    if form.get('plateUmpireAddable'): writable['editRules']['plateUmpireAddable'] = True
    else: writable['editRules']['plateUmpireAddable'] = False
    if form.get('hasField1Umpire'): writable['editRules']['hasField1Umpire'] = True
    else: writable['editRules']['hasField1Umpire'] = False
    if form.get('field1UmpireAddable'): writable['editRules']['field1UmpireAddable'] = True
    else: writable['editRules']['field1UmpireAddable'] = False
    if form.get('hasFieldRequest'): writable['editRules']['hasFieldRequest'] = True
    else: writable['editRules']['hasFieldRequest'] = False
    if form.get('fieldRequestAddable'): writable['editRules']['fieldRequestAddable'] = True
    else: writable['editRules']['fieldRequestAddable'] = False
    if form.get('removable'): writable['editRules']['removable'] = True
    else: writable['editRules']['removable'] = False
    
    if form['plateUmpire'] != "None":
        writable['plateUmpire'] = getUser(_id=form['plateUmpire'])['userId']
    if form['field1Umpire'] != "None":
        writable['field1Umpire'] = getUser(_id=form['field1Umpire'])['userId']
    if form['fieldRequest'] != "None":
        writable['fieldRequest'] = getUser(_id=form['fieldRequest'])['userId']

    eventData.insert_one(writable)
    print(f"Event Added: {writable} by {user['userId']}")
    return True

def getTeamInfo(teamId):
    team = teamData.find_one({'teamId': teamId})
    return team

def updateTeam(user, team, form):
    teamId = team['teamId']
    writable = {
        'teamName': form['teamName'],
        'teamAgeGroup': form['teamAgeGroup'],
        'wins': int(form['wins']),
        'losses': int(form['losses']),
        'ties': int(form['ties']),
    }
    teamData.update_one({'teamId': teamId}, {'$set': writable})
    print(f"Team Updated: {teamId} by {user['userId']}")
    return f"Successfully updated {teamId}"

def deleteTeam(user, teamId):
    teamData.delete_one({'teamId': teamId})
    print(f"Team Deleted: {teamId} by {user['userId']}")
    return f"Successfully deleted {teamId}"

def addTeam(user, form):
    writable = {
        'teamId': form['codePrefix'] + form['codeNum'],
        'location': user['location'],
        'teamName': form['teamName'],
        'teamAgeGroup': form['teamAgeGroup'],
        'wins': 0,
        'losses': 0,
        'ties': 0,
    }
    duplicateCode = teamData.find_one({'teamId': writable['teamId']})
    
    if duplicateCode:
        return f"Error: Team codes must be unique, {writable['teamId']} already exists."
    else:
        teamData.insert_one(writable)
        return True

def updateFieldStatus(venueId, status, sendAlert=True):
    venue = venueData.find_one_and_update({'venueId': venueId}, {'$set': {'status': status}})
    if sendAlert:
        emailUsers = getUserList({'emailNotifications': True})
        emailList = server.createEmailList(emailUsers)
        msgList = []
        for user in emailList:
            msg = send_mail.ChalklineEmail(
                subject=f"{venue['name']} Status Update: {status}",
                recipients=[user],
                html=render_template("emails/field-status.html", venue=venue['name'], status=status)
            )
            msgList.append(msg)
            
        send_mail.sendBulkMail(msgList)

    return f"{venue['name']} field status updated."    

def getVenues(league, criteria={}):
    criteria.update({'location': league})
    venues = venueData.find(criteria)
    venueList = []
    for venue in venues:
        venue['_id'] = str(venue['_id'])
        venueList.append(venue)
    
    return venueList

def sendPasswordReset(email):
    token = str(uuid.uuid4())
    
    user = userData.find_one({'email': email})
    if user is None:
        return "Error: User not found."
    elif 'reset_token' in user:
        return "Error: Password Reset email already sent."
    
    userData.update_one({'email': email}, {'$set': {'reset_token': token}})
    
    message = send_mail.ChalklineEmail(
        subject="Chalkline: Reset Password",
        recipients=[email],
        html=render_template("emails/password-reset.html", email=email, token=token)
    )
    print(f"Password Reset Sent: {email}")
    send_mail.sendMail(message)
    return f"Password Reset email sent to {email}"

def getRentalList(teamId=None, admin=False):
    if admin:
        rentals = rentalData.find({})
    else:
        team = teamData.find_one({'teamId': teamId})
        ageGroup = team['teamAgeGroup']
        rentals = rentalData.find({'active': True, 'ageGroups': ageGroup})
        
    rentalList = []
    for item in rentals:
        item['_id'] = str(item['_id'])
        rentalList.append(item)
    return rentalList

def rentEquipment(user, eventId, rentalName, admin=False):
    event = eventData.find_one({'_id': bson.ObjectId(eventId)})
    if not event:
        return "Error: Event not found."
    
    if rentalName == 'None':
        rentalData.find_one_and_update({'rentalDates.event': eventId}, {'$pull': {'rentalDates': {'event': eventId}}})
        return "Successfully removed rental."
    
    rental = rentalData.find_one({'name': rentalName, 'rentalDates.event': {'$ne': eventId}})
    if not rental:
        return
    
    if 'coach' not in user['role'] and 'admin' not in user['role']:
        return "Error: You do not have permission to rent equipment."
    
    current_rental = rentalData.find_one({'$and': [{'rentalDates.renter': user['userId']}, {'rentalDates.returned': False}, {'end': {'$lt': server.todaysDate()}}]})
    if current_rental and not admin:
        return f"Error: You have not returned {current_rental['name']} ({current_rental['desc']})"
    
    for slot in rental['rentalDates']:
        if (slot['start'] <= event['eventDate'] < slot['end']) and not(slot['returned']):
            return f"Error: This equipment has already been rented for {slot['start'].strftime('%m/%d at %H:%M')}"
    
    rentalData.update_one(rental, {'$push': {'rentalDates': 
        {'renter': user['userId'], 
        'start': event['eventDate'],
        'end': event['eventDate'] + datetime.timedelta(hours=2),
        'event': str(event['_id']),
        'returned': False}
    }})
    
    print(f"Rental: {rentalName} by {user['userId']} for {event['eventDate'].strftime('%m/%d at %H:%M')}")
    return f"Successfully rented {rentalName} for {event['eventDate'].strftime('%m/%d at %H:%M')}"

def returnRental(user, eventId):
    rental = rentalData.update_one({'rentalDates.event': eventId}, {'$set': {'rentalDates.$.returned': True}})
    if rental:
        print(f"Rental Return: {user['userId']} for {eventId}")
        return f"Successfully returned equipment!"
    else:
        return "Error: No rental found."