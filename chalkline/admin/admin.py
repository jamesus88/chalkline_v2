from chalkline.core import ObjectId, now, remove_dups
from flask import render_template
from pymongo import UpdateOne
from datetime import datetime, timedelta
from chalkline.core.user import User
from chalkline.core.team import Team

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
            multi_attrs = ['groups', 'permissions']
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
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'groups.{league['leagueId']}': {'$in': ["umpire"]}}, 
            {'$push': {f'permissions.{league['leagueId']}': "umpire_add"}}
        )

    @staticmethod
    def umpire_add_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'groups.{league['leagueId']}': {'$in': ["umpire"]}}, 
            {'$pull': {f'permissions.{league['leagueId']}': "umpire_add"}}
        )

    @staticmethod
    def umpire_remove_all(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'groups.{league['leagueId']}': {'$in': ["umpire"]}}, 
            {'$push': {f'permissions.{league['leagueId']}': "umpire_remove"}}
        )

    @staticmethod
    def umpire_remove_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'groups.{league['leagueId']}': {'$in': ["umpire"]}}, 
            {'$pull': {f'permissions.{league['leagueId']}': "umpire_remove"}}
        )
    
    @staticmethod
    def coach_add_all(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'groups.{league['leagueId']}': {'$in': ["coach"]}}, 
            {'$push': {f'permissions.{league['leagueId']}': {"$each": ["coach_add", "coach_remove"]}}}
        )

    @staticmethod
    def coach_add_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'groups.{league['leagueId']}': {'$in': ["coach"]}}, 
            {'$pull': {f'permissions.{league['leagueId']}': "coach_add"}}
        )

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

        
            
