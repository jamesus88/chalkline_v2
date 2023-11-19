from chalkline.db import directorData, authenticate
from chalkline.server import safeUser, todaysDate
import pymongo, bson
def getShiftList(userList=[], user=None, criteria={}, hidePast=True):
    criteria['location'] = 'Sarasota'
    if hidePast:
        criteria['endDateTime'] = {'$gte': todaysDate()}

    shifts = directorData.find(criteria).sort('startDateTime', pymongo.ASCENDING)
    shiftList = []
    
    for shift in shifts:
        
        if user is not None:
            if shift['director'] != user['userId']:
                continue
        
        shift['_id'] = str(shift['_id'])
        
        shift['directorInfo'] = {
            'firstName': None,
            'lastName': None,
            'fLast': None,
            'email': None,
            'phone': None
        }
        
        for user in userList:
            if shift['director'] == user['userId']:
                shift['directorInfo']['firstName'] = user['firstName']
                shift['directorInfo']['lastName'] = user['lastName']
                shift['directorInfo']['fLast'] = user['firstName'][0] + '. ' + user['lastName']
                if not user['hideEmail']:
                    shift['directorInfo']['email'] = user['email']
                if not user['hidePhone']:
                    shift['directorInfo']['phone'] = user['phone']
        
        shift.pop('director')
        shiftList.append(shift)
        
    return shiftList
        
def addDirector(shiftId, user):
    shift = directorData.find_one({'_id': bson.ObjectId(shiftId)})
    if shift['director'] is not None:
        return "Error: shift no longer available"
    
    directorData.update_one({'_id': bson.ObjectId(shiftId)}, {'$set': {'director': user['userId']}})
    return 'Successfully added shift!'

def removeDirector(shiftId, user):
    directorData.update_one({'_id': bson.ObjectId(shiftId)}, {'$set': {'director': None}})
    return 'Successfully removed shift!'

def getDirector(userList):
    now = todaysDate()
    shift = directorData.find_one({'startDateTime': {'$lte': now}, 'endDateTime': {'$gte': now}})
    
    if shift:
        for user in userList:
            print(f'{user["userId"]=}')
            print(f'{shift["director"]=}')
            if user['userId'] == shift['director']:
                return safeUser(user)
        
    return {'firstName': None, 'lastName': None, 'fLast': None, 'email': None, 'phone': None}