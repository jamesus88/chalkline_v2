import datetime
import server, db

class EventFilter:
    hidePast = True
    ageGroups = ['T-Ball', 'Coach Pitch', 'AA', 'AAA', 'Majors', '50/70', 'Juniors']
    teamId = []
    field = []
    time = []
    hidePractices = False
    hideGames = False
    hideUmpireDuties = False
    
def getEventList(filter=EventFilter):
    now = server.todaysDate()
    criteria = []
    
    if filter.hidePast:
        criteria.append({'eventDate': {'gte': now}})
    
    criteria.append({'eventAgeGroup': filter.ageGroups})
    
    if len(filter.teamId) > 0:
        team_in_game = [{'awayTeam': {"$in": filter.teamId}}, {'homeTeam': {"$in": filter.teamId}}]
        if not filter.hideUmpireDuties: team_in_game.append({'umpireDuty': {"$in": filter.teamId}})
        criteria.append({'$or': team_in_game})
        
    if len(filter.field) > 0:
        criteria.append({'eventField': {'$in': filter.field}})
    
    if filter.hideGames: criteria.append({'eventType': {'$ne': 'game'}})
    if filter.hidePractices: criteria.append({'eventType': {'$ne': 'practice'}})

    
    events = db.eventData.find({"$and": criteria})
    
    eventList = []
    
    if len(filter.time) > 0:
        for event in events:
            if event['eventDate'].strftime('%H:%M') in filter.time:
                eventList.append(event)
    else:
        eventList = list(events)
        
    eventList.sort(key= lambda x: x['eventDate'], reverse=True)
    
    return eventList

        