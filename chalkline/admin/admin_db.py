from chalkline.db import userData, eventData

def openFreeDrop(criteria={}):
    criteria['eventType'] = 'Game'
    eventData.update_many(criteria, {'$set': {'editRules.requireRemoveRequest': False}})   
    return "Free Drop is now enabled. Umpires can drop all games without approval."

def closeFreeDrop(criteria={}):
    eventData.update_many(criteria, {'$set': {'editRules.requireRemoveRequest': True}})   
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
    #eventData.update_many(criteria, {'$set': {'editRules.requireFieldRequest': False}})
    return "Events have been updated with a predefined method. Contact a developer immediately if this function was accidentally run."