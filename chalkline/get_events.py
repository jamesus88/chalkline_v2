from chalkline import server, db

class EventFilter:
    hidePast = True
    ageGroup = None
    teamId = None
    field = None
    time = None
    eventType = None
    
    def update(self, form):
        if form['hidePast'] == 'False':
            self.hidePast = False
                
        if form.get('teamId') not in  ['null', None]:
            self.teamId = form['teamId']
                
        if form.get('eventType') not in ['null', None]:
            self.eventType = form['eventType']
            
        if form.get('ageGroup') not in ['null', None]:
            self.ageGroup = form['ageGroup']
            
    def __repr__(self) -> str:
        return f'{self.hidePast=}, {self.teamId=}, {self.eventType=}'
    
    def asdict(self) -> dict:
        filterAsDict = {
            'hidePast': str(self.hidePast),
            'ageGroup': self.ageGroup,
            'teamId': self.teamId,
            'field': self.field,
            'eventType': self.eventType
        }
            
        return filterAsDict
            
        
    
def getEventList(filter=EventFilter):
    now = server.todaysDate()
    criteria = [{}]
    
    if filter.hidePast:
        criteria.append({'eventDate': {'$gte': now}})
    
    if filter.ageGroup is not None:
        criteria.append({'eventAgeGroup': filter.ageGroup})
    
    if filter.teamId is not None:
        criteria.append({'$or': [{'awayTeam': filter.teamId}, {'homeTeam': filter.teamId}, {'umpireDuty': filter.teamId}]})
        
    if filter.field is not None:
        criteria.append({'eventField': filter.field})
        
    if filter.eventType is not None:
        criteria.append({'eventType': filter.eventType})

    print(f'{criteria=}')
    events = db.eventData.find({"$and": criteria})

    eventList = []

    if filter.time is not None:
        for event in events:
            if event['eventDate'].strftime('%H:%M') == filter.time:
                eventList.append(event)
    else:
        eventList = list(events)
        
    eventList.sort(key= lambda x: x['eventDate'], reverse=True)
    
    return eventList

        