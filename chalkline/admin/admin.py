from chalkline.core import ObjectId, now, remove_dups
from flask import render_template
from pymongo import UpdateOne
from datetime import datetime, timedelta
from chalkline.core.user import User
from chalkline.core.team import Team
from pandas import read_csv
import chalkline.core.mailer as mailer
from chalkline.core.director import Shift
from chalkline.core.events import Event, Filter
from chalkline.core.league import League


class Admin:

    @staticmethod
    def update_all(form, cls, league):
        updates = {}

        for key, value in form.items():
            if '_' not in key or 'filter' in key:
                continue

            _id, attr = key.split('_')

            # formatting
            date_attrs = ['date', 'start_date', 'end_date']
            int_attrs = ['field']
            float_attrs = ['duration']
            multi_attrs = ['groups']
            league_specific = ['groups', 'permissions']
            ump_attrs = Event.get_all_ump_positions()


            if value == "None": value = None

            if attr in date_attrs:
                value = datetime.strptime(value, "%Y-%m-%dT%H:%M")
            elif attr in int_attrs:
                value = int(value)
            elif attr in float_attrs:
                value = float(value)
            elif attr in multi_attrs:
                value = form.getlist(key)

            if attr in league_specific:
                attr = f"{attr}.{league['leagueId']}"

            if attr in ump_attrs:
                attr = f"umpires.{attr}.user"
                if value in ['', "None"]: value = None

            # append to updates

            if _id not in updates:
                updates[_id] = {attr: value}
            else:
                updates[_id][attr] = value
        
        writes = []
        for key, map in updates.items():
            writes.append(UpdateOne({'_id': ObjectId(key)}, {'$set': map}))

        cls.col.bulk_write(writes)

        return updates
    
    @staticmethod
    def send_updates(old_events, updates):
        for e in old_events:
            if e['_id'] in updates:
                new = updates[e['_id']]

                if (
                    new['status'] != e['status'] or
                    new['date'] != e['date'] or
                    new['field'] != e['field'] or
                    new['venueId'] != e['venueId']
                ):
                    
                    users = Event.get_users_in_event(e)
                    emails = []
                    for u in users:
                        if u['preferences']['email_nots']:
                            msg = mailer.ChalklineEmail(
                                subject=f"Event Update!",
                                recipients=[u['email']],
                                html=render_template("emails/event-update.html", old=e, new=new)
                            )
                            emails.append(msg)

                    mailer.sendBulkMail(emails)

    @staticmethod
    def delete(cls, id):
        cls.col.delete_one({'_id': ObjectId(id)})

    @staticmethod
    def toggle_perm(league, perm):
        League.col.update_one({'leagueId': league['leagueId']}, {"$set": {perm: not(league[perm])}})

    @staticmethod
    def umpire_add_all(league):
        League.col.update_one({'leagueId': league['leagueId']}, {"$push": {"perm_groups.$[].perms": "umpire_add"}})

    @staticmethod
    def umpire_add_none(league):
        League.col.update_one({'leagueId': league['leagueId']}, {"$pull": {"perm_groups.$[].perms": "umpire_add"}})

    @staticmethod
    def umpire_remove_all(league):
        League.col.update_one({'leagueId': league['leagueId']}, {"$push": {"perm_groups.$[].perms": "umpire_remove"}})

    @staticmethod
    def umpire_remove_none(league):
        League.col.update_one({'leagueId': league['leagueId']}, {"$pull": {"perm_groups.$[].perms": "umpire_remove"}})
    
    @staticmethod
    def coach_add_all(league):
        League.col.update_one({'leagueId': league['leagueId']}, {"$pull": {"perm_groups.$[].perms": "coach_add"}})

    @staticmethod
    def coach_add_none(league):
        League.col.update_one({'leagueId': league['leagueId']}, {"$pull": {"perm_groups.$[].perms": "coach_add"}})

    @staticmethod
    def generate_dod_shifts(league):

        Shift.col.delete_many({'leagueId': league['leagueId']})

        filters = Filter.default()
        filters['end'] = now() + timedelta(days=365)
        events = Event.get(league, filters=filters)

        count = 0
        for venue in league['venues']:
            dates = remove_dups([e['date'] for e in events if e['venueId'] == venue])
            shifts = []

            for i in range(len(dates)):
                if len(shifts) != 0:
                    diff = dates[i] - shifts[-1]['start_date']
                    if diff < timedelta(hours=Shift.SHIFT_LENGTH):
                        continue

                shifts.append(Shift.create(
                    league=league,
                    form={
                        'venueId': venue,
                        'start-date': (dates[i] - timedelta(minutes=30)).isoformat()[:16],
                        'end-date': (dates[i] - timedelta(minutes=30) + timedelta(hours=Shift.SHIFT_LENGTH)).isoformat()[:16]
                    }, insert=False
                ))

            if len(shifts) > 0: Shift.col.insert_many(shifts)

            count += len(shifts)

        return count

    @staticmethod
    def read_schedule(res, file):
        events = []
        errors = set()
        team_codes = {t['teamId'] for t in res['league']['teams']}
        team_codes.add(None)

        df = read_csv(file)
        df = df.replace({float('nan'): None}) # replace NaN with None

        # strip all string cols
        str_col = df.select_dtypes('object')
        df[str_col.columns] = str_col.apply(lambda x: x.str.strip())

        # check for errors
        if len(set(df['type'].unique()).difference({'Game', 'Practice'})) > 0:
            raise ValueError('One or more event types are invalid. Choose from "Game" or "Practice"')
        
        if len(set(df['venueId'].unique()).difference(set(res['league']['venues']))) > 0:
            raise ValueError(f'One or more venues are invalid. Choose from {", ".join(res['league']['venues'])} or create new ones.')
        
        if len(set(df['age'].unique()).difference(set(res['league']['age_groups']))) > 0:
            raise ValueError(f'One or more ages are invalid. Choose from {", ".join(res['league']['age_groups'])} or create new ones.')
        
        if len(set(df['away'].unique()).difference(team_codes)) > 0:
            errors.add('One or more away teams are invalid. Choose a team code from your league or create a new one.')

        if len(set(df['home'].unique()).difference(team_codes)) > 0:
            errors.add('One or more home teams are invalid. Choose a team code from your league or create a new one.')

        for i, r in df.iterrows():
            e = Event.default()
            e['leagueId'] = res['league']['leagueId']
            e['type'] = r.type
            e['season'] = r.season
            if r.season != res['league']['current_season']:
                errors.add(f"One or more games are not listed for your league's current season ({res['league']['current_season']})")
            e['date'] = datetime.strptime(r.date + ' ' + r.time, '%Y-%m-%d %H:%M')
            e['duration'] = float(r.length_hrs)
            e['venueId'] = r.venueId
            e['field'] = int(r.field)
            e['age'] = r.age
            e['away'] = r.away
            e['home'] = r.home
            e['status'] = r.status.title() if r.status else "On Time"
            e['locked'] = True if r.locked else False
            if e['locked']:
                errors.add("One or more games are locked.")
            e['created'] = now()

            for pos in Event.get_all_ump_positions():
                if getattr(r, pos.lower()):
                    blank = Event.generate_blank_ump_pos(e, pos)
                    if getattr(r, pos.lower()+"_duty"):
                        blank['team_duty'] = getattr(r, pos.lower()+"_duty")
                        if blank['team_duty'] not in team_codes:
                            errors.add("One or more umpire duties include invalid teams. Choose a team code from your league or create a new one.")

                    e['umpires'][pos] = blank

            events.append(e)

        return events, errors
