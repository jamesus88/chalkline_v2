import pymongo, bson, datetime 
import chalkline.server as server
import os

client = pymongo.MongoClient(os.environ.get('PYMONGO_CLIENT'), connect=False)
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

def authenticate(userId = ''):
    user = userData.find_one({'userId': userId})
    if user:
        user['_id'] = str(user['_id'])
        user = appendPermissions(user)
        
        print('login: ', user)
        
        return user
    else:
        return None

def appendPermissions(user):
    permissionSet = permissions.find_one({'set': user['permissionSet']})
    permissionSet.pop('_id')
    user['permissions'] = permissionSet
    
    return user

def getUserList(criteria={}):
    return list(userData.find(criteria))

def checkDuplicateUser(newUser):
    user = userData.find_one({"$or": [{'userId': newUser['userId']}, {'email': newUser['email']}, {'phone': newUser['phone']}]})
    if user: return True
    else: return False
    
def createUser(form):
    response = {
        'newUser': {
          "location": form['location'],
          "firstName": form['firstName'],
          "lastName": form['lastName'],
          "email": form['email'],
          "phone": form['phone'],
          "sms-gateway": form.get('carrier'),
          "userId": form['userId'],
          "role": [],
          "teams": [],
          "permissionSet": "C0",
          "canRemoveGame": False,
          "emailNotifications": True,
          "phoneNotifications": True,
          "hideEmail": False,
          "hidePhone": False
        },
        'error': None
    }
    
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

def addPlate(user, gameId):
    criteria = [{'_id': bson.ObjectId(gameId)}, {'plateUmpire': None}, {'eventAgeGroup': {'$nin': user['permissions']['prohibitedPlate']}}]
    
    game = eventData.find_one_and_update({'$and': criteria}, {'$set': {'plateUmpire': user['userId']}})
    
    if game:
        msg = f'Successfully added {user["firstName"][0]}. {user["lastName"]} for plate duty.'
    else:
        msg = 'Error: position filled or unavailable'
        
    return msg

def addField1(user, gameId):
    criteria = [{'_id': bson.ObjectId(gameId)}, {'field1Umpire': None}, {'eventAgeGroup': {'$nin': user['permissions']['prohibitedField']}}]
    
    game = eventData.find_one_and_update({'$and': criteria}, {'$set': {'field1Umpire': user['userId']}})
    
    if game:
        msg = f'Successfully added {user["firstName"][0]}. {user["lastName"]} for field duty.'
    else:
        msg = 'Error: position filled or unavailable'
        
    return msg

def removeGame(user, gameId):
    game = eventData.find_one({'_id': bson.ObjectId(gameId)})
    setData = {}
    if (not game['editRules']['requireRemoveRequest']) or user['canRemoveGame']:
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
    
    else:
        msg = 'Error: you do not have permission to request a field umpire for this game.'
        
    return msg

def getEventInfo(eventId, add_criteria={}):
    add_criteria['_id'] = bson.ObjectId(eventId)
    return eventData.find_one(add_criteria)

def updateEvent(event, form, userList, editRules=False, editContacts=False):
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
        if form.get('plateUmpireAddable'): writable['editRules']['plateUmpireAddable'] = True
        else: writable['editRules']['plateUmpireAddable'] = False
        if form.get('field1UmpireAddable'): writable['editRules']['field1UmpireAddable'] = True
        else: writable['editRules']['field1UmpireAddable'] = False
        if form.get('fieldRequestAddable'): writable['editRules']['fieldRequestAddable'] = True
        else: writable['editRules']['fieldRequestAddable'] = False
        if form.get('requireRemoveRequest'): writable['editRules']['requireRemoveRequest'] = True
        else: writable['editRules']['requireRemoveRequest'] = False
        if form.get('fieldRequestRemovable'): writable['editRules']['fieldRequestRemovable'] = True
        else: writable['editRules']['fieldRequestRemovable'] = False
    
    eventData.update_one({'_id': bson.ObjectId(event['_id'])}, {'$set': writable})
    
    return 'Successfully updated event.'

def deleteEvent(eventId, ignoreDate=False):
    criteria = {'_id': bson.ObjectId(eventId)}
    event = eventData.find_one(criteria)
    if event['eventDate'] < server.todaysDate() or ignoreDate:
        return "Error: cannot edit past events"
    else:
        eventData.delete_one(criteria)
        return "Successfully deleted game"
    
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
    if form.get('plateUmpireAddable'): writable['editRules']['plateUmpireAddable'] = True
    else: writable['editRules']['plateUmpireAddable'] = False
    if form.get('field1UmpireAddable'): writable['editRules']['field1UmpireAddable'] = True
    else: writable['editRules']['field1UmpireAddable'] = False
    if form.get('fieldRequestAddable'): writable['editRules']['fieldRequestAddable'] = True
    else: writable['editRules']['fieldRequestAddable'] = False
    if form.get('requireRemoveRequest'): writable['editRules']['requireRemoveRequest'] = True
    else: writable['editRules']['requireRemoveRequest'] = False
    if form.get('fieldRequestRemovable'): writable['editRules']['fieldRequestRemovable'] = True
    else: writable['editRules']['fieldRequestRemovable'] = False
    
    if form['plateUmpire'] != "None":
        writable['plateUmpire'] = form['plateUmpire']
    if form['field1Umpire'] != "None":
        writable['field1Umpire'] = form['field1Umpire']
    if form['fieldRequest'] != "None":
        writable['fieldRequest'] = form['fieldRequest']

    eventData.insert_one(writable)
    
    return True

def getTeamInfo(teamId):
    team = teamData.find_one({'teamId': teamId})
    return team

def updateTeam(team, form):
    teamId = team['teamId']
    writable = {
        'teamName': form['teamName'],
        'teamAgeGroup': form['teamAgeGroup'],
        'wins': int(form['wins']),
        'losses': int(form['losses']),
        'ties': int(form['ties']),
    }
    teamData.update_one({'teamId': teamId}, {'$set': writable})
    return f"Successfully updated {teamId}"

def deleteTeam(teamId):
    teamData.delete_one({'teamId': teamId})
    return f"Successfully deleted {teamId}"

def addTeam(user, form):
    writable = {
        'teamId': form['codePrefix'] + form['codeNum'],
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
        server.sendMail(
            subject=f"{venue['name']} field status: {status}",
            body=f"Sarasota Little League has updated {venue['name']} field status to {status}. Visit www.chalklinebaseball.com/league/status for more info.\nwww.chalklinebaseball.com",
            recipients=emailList
        )
        
        phoneUsers = getUserList({'phoneNotifications': True})
        phoneList = server.createPhoneList(phoneUsers)
        server.sendMail(
            subject=None,
            body=f"Sarasota Little League has updated {venue['name']} field status to {status}. Visit www.chalklinebaseball.com/league/status for more info.\nwww.chalklinebaseball.com",
            recipients=phoneList
        )
    return f"{venue['name']} field status updated."    

def getVenues(league, criteria={}):
    criteria.update({'location': league})
    venues = venueData.find(criteria)
    venueList = []
    for venue in venues:
        venue['_id'] = str(venue['_id'])
        venueList.append(venue)
    
    return venueList
