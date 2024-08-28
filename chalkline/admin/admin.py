from chalkline.core import mailer, ObjectId, now, remove_dups
from pymongo import UpdateOne
from datetime import datetime, timedelta
from chalkline.core.user import User
from chalkline.core.director import Shift
from chalkline.core.events import Event, Filter

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
            multi_attrs = ['groups', 'permissions']
            league_specific = ['groups', 'permissions']

            if attr in date_attrs:
                value = datetime.strptime(value, "%Y-%m-%dT%H:%M")
            elif attr in int_attrs:
                value = int(value)
            elif attr in multi_attrs:
                value = form.getlist(key)

            if attr in league_specific:
                attr = f"{attr}.{league['leagueId']}"

            # append to updates

            if _id not in updates:
                updates[_id] = {attr: value}
            else:
                updates[_id][attr] = value
        
        writes = []
        for key, map in updates.items():
            writes.append(UpdateOne({'_id': ObjectId(key)}, {'$set': map}))

        cls.col.bulk_write(writes)

    @staticmethod
    def delete(cls, id):
        cls.col.delete_one({'_id': ObjectId(id)})

    @staticmethod
    def umpire_add_all(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'{league['abbr']}-groups': {'$in': ["umpire"]}}, 
            {'$push': {f'{league['abbr']}-permissions': "umpire_add"}}
        )

    @staticmethod
    def umpire_add_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'{league['abbr']}-groups': {'$in': ["umpire"]}}, 
            {'$pull': {f'{league['abbr']}-permissions': "umpire_add"}}
        )

    @staticmethod
    def umpire_remove_all(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'{league['abbr']}-groups': {'$in': ["umpire"]}}, 
            {'$push': {f'{league['abbr']}-permissions': "umpire_remove"}}
        )

    @staticmethod
    def umpire_remove_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'{league['abbr']}-groups': {'$in': ["umpire"]}}, 
            {'$pull': {f'{league['abbr']}-permissions': "umpire_remove"}}
        )
    
    @staticmethod
    def coach_add_all(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'{league['abbr']}-groups': {'$in': ["coach"]}}, 
            {'$push': {f'{league['abbr']}-permissions': "coach_add"}}
        )

    @staticmethod
    def coach_add_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, f'{league['abbr']}-groups': {'$in': ["coach"]}}, 
            {'$pull': {f'{league['abbr']}-permissions': "coach_add"}}
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

        
            
