import pymongo, bson
from flask import session

client = pymongo.MongoClient("mongodb+srv://aidanhurwitz:Mongo4821@mongo.to6zmzr.mongodb.net/?retryWrites=true&w=majority", connect=False)
db = client['chalkline']

eventData = db['test_eventData']
userData = db['test_userData']
permissions = db['permissions']
reportData = db['test_reportData']
teamData = db['test_teamData']
playerData = db['test_playerData']

def authenticate(userId = ''):
    user = userData.find_one({'userId': userId})
    if user:
        user['_id'] = str(user['_id'])
        return user
    else:
        return None

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
          "userId": form['userId'],
          "role": [],
          "child": [],
          "teams": [],
          "emailNotifications": True,
          "textNotifications": True
        },
        'error': None
    }
    
    if form.get('role-coach'):
        response['newUser']['role'].append('coach')
    if form.get('role-parent'):
        response['newUser']['role'].append('parent')
    if form.get('role-umpire'):
        response['newUser']['role'].append('umpire')
    if form.get('role-youth'):
        response['newUser']['role'].append('youth')
    if form.get('role-board'):
        response['newUser']['role'].append('board')
        
    if len(response['newUser']['role']) < 1:
        response['error'] = 'Select at least one account role'
        
    if checkDuplicateUser(response['newUser']):
        response['error'] = 'User ID, email, or phone number already exists. Try logging in...'
    print(response)
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
        'phoneNotifications': False
    }
    
    if form.get('emailNotifications'):
        writable['emailNotifications'] = True
    if form.get('phoneNotifications'):
        writable['phoneNotifications'] = True
    
    user = userData.find_one_and_update({'userId': userId}, {'$set': writable}, return_document=pymongo.ReturnDocument.AFTER)
    user['_id'] = str(user['_id'])
    return user

def getTeamsFromUser(teamCodes):
    teams = teamData.find({"teamId": {"$in": teamCodes}})
    teamsList = []
    
    for team in teams:
        team['_id'] = str(team['_id'])
        teamsList.append(team)
    
    return teamsList

def removeTeamFromUser(user, teamCode):
    user['teams'].remove(teamCode)
    user = userData.find_one_and_update({"userId": user['userId']}, {"$set": {"teams": user['teams']}}, return_document=pymongo.ReturnDocument.AFTER)
    user['_id'] = str(user['_id'])
    return user

def addTeamToUser(user, teamCode):
    if teamCode in user['teams']:
        return "Error - team already added."
    elif not teamData.find_one({"teamId": teamCode}):
        return "Error - team code does not exist."
    
    user['teams'].append(teamCode)
    user = userData.find_one_and_update({"userId": user['userId']}, {"$set": {"teams": user['teams']}}, return_document=pymongo.ReturnDocument.AFTER)
    user['_id'] = str(user['_id'])
    return user