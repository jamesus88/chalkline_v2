from chalkline.db import directorData
from chalkline.server import safeUser, todaysDate
import pymongo, bson, datetime

def getShiftList(location, userList=[], add_criteria={}, hidePast=True):
    criteria = [add_criteria, {'location': location}]
    if hidePast:
        criteria.append({'endDateTime': {'$gte': todaysDate()}})

    shifts = directorData.find({'$and': criteria}).sort('endDateTime', pymongo.ASCENDING)
    shiftList = []
    
    for shift in shifts:
        shift['_id'] = str(shift['_id'])
        
        shift['directorInfo'] = {
            '_id': None,
            'firstName': None,
            'lastName': None,
            'fLast': None,
            'email': None,
            'phone': None
        }
        
        for director in userList:
            if shift['director'] == director['userId']:
                shift['directorInfo'] = {
                    '_id': str(director['_id']),
                    'firstName': director['firstName'],
                    'lastName': director['lastName'],
                    'fLast': director['firstName'][0] + '. ' + director['lastName'],
                    'email': director['email'],
                    'phone': director['phone']
                }
                break
        
        shift.pop('director')
        shiftList.append(shift)
    

    return shiftList
        
def addDirector(shiftId, user):
    shift = directorData.find_one({'_id': bson.ObjectId(shiftId)})
    if shift['director'] is not None:
        return "Error: shift no longer available"
    
    directorData.update_one({'_id': bson.ObjectId(shiftId)}, {'$set': {'director': user['userId']}})
    return 'Successfully added shift'

def removeDirector(shiftId, user):
    directorData.update_one({'_id': bson.ObjectId(shiftId)}, {'$set': {'director': None}})
    return 'Successfully removed shift'

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

def getShiftInfo(shiftId, userList):
    shift = directorData.find_one({'_id': bson.ObjectId(shiftId)})
    shift['_id'] = str(shift['_id'])
    
    shift['directorInfo'] = {
        '_id': None,
        'firstName': None,
        'lastName': None,
        'fLast': None,
        'email': None,
        'phone': None
    }
    
    for user in userList:
        if user['userId'] == shift['director']:
            s_user = safeUser(user)
            shift['directorInfo'] = {
                '_id': s_user['_id'],
                'firstName': s_user['firstName'],
                'lastName': s_user['lastName'],
                'fLast': s_user['fLast'],
                'email': s_user['email'],
                'phone': s_user['phone']
            }
            
    return shift

def updateShift(shiftId: str, form: dict, userList: list):
    writable = {
        'startDateTime': datetime.datetime.strptime(form['startDateTime'], "%Y-%m-%dT%H:%M"),
        'endDateTime': datetime.datetime.strptime(form['endDateTime'], "%Y-%m-%dT%H:%M"),
        'director': None
    }
    for user in userList:
        if str(user['_id']) == str(form['director']):
            writable['director'] = user['userId']
            
    directorData.update_one({'_id': bson.ObjectId(shiftId)}, {'$set': writable})
    return "Successfully updated shift"

def deleteShift(shiftId):
    directorData.delete_one({'_id': bson.ObjectId(shiftId)})
    return "Deleted one shift"
    
def addShift(location, user, form):
    writable = {
        'location': location,
        'startDateTime': datetime.datetime.strptime(form['startDateTime'], "%Y-%m-%dT%H:%M"),
        'endDateTime': datetime.datetime.strptime(form['endDateTime'], "%Y-%m-%dT%H:%M"),
        'director': None
    }
    
    directorData.insert_one(writable)
    
    return True