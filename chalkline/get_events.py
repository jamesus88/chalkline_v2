from chalkline import server, db
import pymongo

class EventFilter:
    hidePast = True
    eventTypeFilter = None
    teamId = None
    ageGroup = None
    admin = False
    
    def __init__(self, args: dict = {}) -> None:
        for key, value in args.items():
            setattr(self, key, value)
    
    def update(self, form):
        if form.get('hidePast'):
            if form['hidePast'] == 'false':
                self.hidePast = False
                
        if form.get('eventTypeFilter'):
            if form['eventTypeFilter'] != 'null':
                self.eventTypeFilter = form['eventTypeFilter']
        
        if form.get('teamId'):
            if form['teamId'] != 'null':
                self.teamId = form['teamId']
                
        if form.get('ageGroup'):
            if form['ageGroup'] != 'null':
                self.ageGroup = form['ageGroup']
                
    def asdict(self):
        return {
            'hidePast': self.hidePast,
            'eventTypeFilter': self.eventTypeFilter,
            'teamId': self.teamId,
            'ageGroup': self.ageGroup
        }
    
    
def getEventList(location, filter=EventFilter, add_criteria={}, safe=True, userList=[]):
    criteria = [{'eventLocation': location}, add_criteria]
    
    if not filter.admin:
       criteria.append({'editRules.visible': True})
    
    if filter.hidePast:
        criteria.append({'eventDate': {'$gte': server.todaysDate(padding_hrs=-6)}})
        
    if filter.eventTypeFilter:
        if filter.eventTypeFilter == 'Umpire Duty':
            criteria.append({'umpireDuty': filter.teamId})
        else:
            criteria.append({'eventType': filter.eventTypeFilter})
            
    if filter.ageGroup:
        criteria.append({'eventAgeGroup': filter.ageGroup})
        
    if filter.teamId:
        if filter.eventTypeFilter == 'Umpire Duty':
            criteria.append({'umpireDuty': filter.teamId})
        elif filter.eventTypeFilter:
            criteria.append({'$or': [{'awayTeam': filter.teamId}, {'homeTeam': filter.teamId}]})
        else:
            criteria.append({'$or': [{'awayTeam': filter.teamId}, {'homeTeam': filter.teamId}, {'umpireDuty': filter.teamId}]})
    
    events = list(db.eventData.find({'$and': criteria}).sort([('eventDate', pymongo.ASCENDING), ('eventField', pymongo.ASCENDING)]))

    for i in range(len(events)):
        if events[i]['umpireDuty'] == filter.teamId and filter.teamId is not None:
            events[i]['eventType'] = 'Umpire Duty'
    if safe:
        events = [server.safeEvent(event, userList) for event in events]
    
    return events
        