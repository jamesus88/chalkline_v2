from chalkline.collections import logsData
from chalkline import server as srv
def log_docs(docs: list[dict]):
    date = srv.todaysDate()
    for doc in docs:
        doc.update({'datetime': date})
    logsData.insert_many(docs)
    print(f'ChalkLog: {len(docs)} messages logged.')

def log(location, log_type, msg=None, userId=None, eventId=None):
    date = srv.todaysDate()
    log = {
        'datetime': date,
        'location': location,
        'type': log_type,
        'desc': msg,
        'userId': userId,
        'eventId': eventId
    }

    logsData.insert_one(log)
    print(f'ChalkLog: {log_type} logged.')

def view_date_range(start, end):
    criteria = {'$gte': start, '$lte': end}
    logs = logsData.find(criteria)
    if logs:
        return list(logs)
    else:
        return None

def view_log_type(log_type):
    logs = logsData.find({'log_type': log_type})
    if logs: return list(logs)
    else: return None

def view_location(location):
    logs = logsData.find({'location': location})
    if logs: return list(logs)
    else: return None

def view_user(userId):
    logs = logsData.find({'userId': userId})
    if logs: return list(logs)
    else: return None

def view_event(eventId):
    logs = logsData.find({'eventId': eventId})
    if logs: return list(logs)
    else: return None
