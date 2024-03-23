from chalkline.db import userData, eventData, rentalData
from bson import ObjectId

def openFreeDrop(criteria={}):
    criteria['eventType'] = 'Game'
    eventData.update_many(criteria, {'$set': {'editRules.removable': True}})   
    return "Free Drop is now enabled. Umpires can drop all games without approval."

def closeFreeDrop(criteria={}):
    eventData.update_many(criteria, {'$set': {'editRules.removable': False}})   
    return "Free Drop is now disabled. All games require permission to be dropped."
    
def unlockGames(criteria={}):
    criteria['eventType'] = 'Game'
    eventData.update_many(criteria, 
        {'$set': {
            'editRules.plateUmpireAddable': True,
            'editRules.field1UmpireAddable': True,
            'editRules.fieldRequestAddable': True,
        }})   
    return "All games are unlocked for umpires and coaches."

def lockGames(criteria={}):
    eventData.update_many(criteria,
        {'$set': {
            'editRules.plateUmpireAddable': False, 
            'editRules.field1UmpireAddable': False,
            'editRules.fieldRequestAddable': False,
        }})
    return "All games are locked for umpires and coaches."

def updateMisc(criteria={}):
    return "Events have been updated with a predefined method. Contact a developer immediately if this function was accidentally run."

def updateRental(user, rentalName, form):
    if 'admin' not in user['role']:
        return "Error: permission denied."
    
    new = {
        'active': True if form['active'] == 'True' else False,
        'desc': form['desc'],
        'ageGroups': form['ageGroups'],
        'field': form['field']
    }
    
    rentalData.update_one({'name': rentalName}, {'$set': new})
    print(f"Rental Update: {user['userId']} updated {rentalName}")
    return f"Successfully updated {rentalName}"
    
def removeReserve(user, rentalName):
    if 'admin' not in user['role']:
        return "Error: permission denied."
    
    rentalData.update_one({'name': rentalName}, {'$set': {'rentalDates': []}})
    print(f"Rental Update: {user['userId']} removed all reservations for {rentalName}")
    return f"Successfully removed reservations for {rentalName}"

def deleteRental(user, rentalName):
    if 'admin' not in user['role']:
        return "Error: permission denied."
    
    rentalData.delete_one({'name': rentalName})
    print(f"Rental Deleted: {user['userId']} deleted {rentalName}")
    return f"Successfully deleted {rentalName}"

def addRental(user, form):
    if rentalData.find_one({'name': form['name']}):
        return "Error: equipment name must be unique."
    
    rentalData.insert_one(form)
    print(f"Rental Added: {user['userId']} added {form['name']}")
    return None

def updateUser(user, target_id, update):
    if 'admin' not in user['role']:
        raise PermissionError('Error: admin credentials required')
    
    target = userData.find_one_and_update({'_id': ObjectId(target_id)}, {'$set': update})
    print(f'User Updated: {target['userId']} by {user['userId']}')
    return f"Successfully updated {target['firstName'][0]}. {target['lastName']}"