import icalendar, datetime, x_wr_timezone
from chalkline import get_events, server as srv

def add_event(cal: icalendar.Calendar, event, role):
    cal_event = icalendar.Event()
    cal_event.add('uid', str(event['_id']))

    cal_event.add('dtstart', event['eventDate'])

    if event['eventAgeGroup'] in ['Majors', '50/70', 'Juniors']:
        game_length = datetime.timedelta(hours=2)
    else:
        game_length = datetime.timedelta(hours=1.5)
    cal_event.add('dtend', event['eventDate'] + game_length)


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
    calendar.add('calscale', 'Gregorian')
    calendar.add('version', '2.0')
    calendar.add('x-wr-timezone', 'America/New_York')

    tz = icalendar.Timezone()
    tz.add('tzid', 'America/New_York')
    
    calendar.add_component(tz)
    
    
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

    return x_wr_timezone.to_standard(calendar).to_ical()