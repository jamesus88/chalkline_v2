import icalendar, datetime, pytz
from chalkline import get_events, server as srv

def add_event(cal: icalendar.Calendar, event, role):
    cal_event = icalendar.Event()
    cal_event.add('uid', str(event['_id']))
    cal_event.add('dtstart', event['eventDate'])

    #convert to utc
    event['eventDate'] = event['eventDate'].replace(tzinfo=pytz.timezone('EST'))

    if event['eventAgeGroup'] in ['Majors', '50/70', 'Juniors']:
        game_length = datetime.timedelta(hours=2)
    else:
        game_length = datetime.timedelta(hours=1.5)
    cal_event.add('dtend', event['eventDate'] + game_length)
    cal_event.add('tzoffsetfrom', datetime.timedelta(hours=-4))
    cal_event.add('tzoffsetto', datetime.timedelta(hours=-5))


    cal_event.add('summary', f"{event['awayTeam']} @ {event['homeTeam']} ({role}) - Chalkline")
    cal_event.add('location', f"{event['eventVenue']} Field {event['eventField']}")
    cal_event.add('description', f"{role} for {event['eventAgeGroup']} game at {event['eventVenue']} Field {event['eventField']}.\n\nCreated by Chalkline Baseball")
    cal_event.add('created', srv.todaysDate())
    cal_event.add('url', f"www.chalklinebaseball.com/view-info/event/{str(event['_id'])}")

    cal.add_component(cal_event)



def serve_calendar(user, start_date=None):
    '''
    called from invite link
    '''
    calendar = icalendar.Calendar()
    calendar.add("prodid", "Chalkline Baseball")
    eventList = []

    eventFilter = get_events.EventFilter()
    eventFilter.hidePast = False

    for location in user['locations']:
        eventList.extend(get_events.getEventList(location, eventFilter, safe=False))

    for event in eventList:
        # umpires
        if user['userId'] == event['plateUmpire']:
            add_event(calendar, event, 'Plate Umpire')
            continue
        elif user['userId'] == event['field1Umpire']:
            add_event(calendar, event, 'Field Umpire')
            continue

        # coaches
        if event['homeTeam'] in user['teams']:
            add_event(calendar, event, 'Home Team')
            continue
        elif event['awayTeam'] in user['teams']:
            add_event(calendar, event, 'Away Team')
            continue

    return calendar.to_ical()




