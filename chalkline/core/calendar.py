import icalendar, datetime, x_wr_timezone
from chalkline.core.events import Event, Filter
from chalkline.core.league import League
from chalkline.core import now

class Calendar:

    def add_event(cal: icalendar.Calendar, event, role):
        cal_event = icalendar.Event()
        cal_event.add('uid', str(event['_id']))

        cal_event.add('dtstart', event['date'])
        cal_event.add('dtend', event['date'] + datetime.timedelta(hours=event['duration']))

        cal_event.add('summary', f"{event['age']} Game - {role} ({event['away']} @ {event['home']})")
        cal_event.add('location', f"{event['venueId']} Field {event['field']}")
        cal_event.add('description', f"{role} for {event['age']} game at {event['venueId']} Field {event['field']}.\n\nCreated by Chalkline Baseball")
        cal_event.add('created', now())
        cal_event.add('url', f"https://www.chalklinebaseball.com/view/event/{str(event['_id'])}")

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

        for location in user['leagues']:
            league = League.get(location)
            filters = Filter.default()
            e = Event.get(league, user, filters=filters, safe=False)
            eventList.extend(e)


        for event in eventList:
            # umpires
            for pos, u in event['umpires'].items():
                if u['user'] == user['userId']:
                    Calendar.add_event(calendar, event, f'{pos} Umpire')
                    continue

            # coaches
            if event['home'] in user['teams']:
                Calendar.add_event(calendar, event, 'Home Team')
                continue
            elif event['away'] in user['teams']:
                Calendar.add_event(calendar, event, 'Away Team')
                continue

        return x_wr_timezone.to_standard(calendar).to_ical()