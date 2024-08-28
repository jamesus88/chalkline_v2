from chalkline.collections import directorData
from datetime import datetime, timedelta
from chalkline.core.user import User
from chalkline.core.league import Venue
from chalkline.core import ObjectId, _safe, now
from chalkline import SEASON

class Filter:
    @staticmethod
    def default():
        return {
            'start': now() - timedelta(hours=2),
            'end': now() + timedelta(days=200),
            'season': SEASON
        }

    @staticmethod
    def parse(form) -> dict:
        filters = Filter.default()

        if form.get('filter_reset'):
            return filters

        if form.get('filter_start'):
            filters['start'] = datetime.strptime(form['filter_start'], "%Y-%m-%dT%H:%M")
        if form.get('filter_end'):
            filters['end'] = datetime.strptime(form['filter_end'], "%Y-%m-%dT%H:%M")

        filters['season'] = form.get('filter_season')
        
        return filters

class Shift:
    col = directorData
    SHIFT_LENGTH = 2

    @staticmethod
    def safe(s):
        s = Shift.load_info(s)
        return _safe(s)

    @staticmethod
    def create(league, form, insert=True):
        shift = {
            'leagueId': league['leagueId'],
            'venueId': form['venueId'],
            'start_date': datetime.strptime(form.get('start-date'), '%Y-%m-%dT%H:%M'),
            'end_date': datetime.strptime(form.get('start-date'), '%Y-%m-%dT%H:%M'),
            'season': SEASON,
            'director': None,
        }
        return shift

    @staticmethod
    def load_info(shift):
        if shift['director']:
            shift['director'] = User.get_user(userId=shift['director'], view=True)
        shift['venue_info'] = Venue.get(shift['venueId'])
        return shift

    @staticmethod
    def add_director(shiftId, user):
        if 'director' not in user['groups']:
            raise PermissionError('You cannot add director shifts.')
        
        Shift.col.update_one({'_id': ObjectId(shiftId)}, {'$set': {'director': user['userId']}})

    @staticmethod
    def remove_director(shiftId):
        Shift.col.update_one({'_id': ObjectId(shiftId)}, {'$set': {'director': None}})

    @staticmethod
    def get(league, user=None, filters=Filter.default(), add_criteria={}):
        criteria = [{'leagueId': league['leagueId']}, add_criteria]

        if filters.get('start'):
            criteria.append({'start_date': {'$gte': filters['start']}})
        if filters.get('end'):
            criteria.append({'end_date': {'$lte': filters['end']}})
        if filters.get('season'):
            criteria.append({'season': filters['season']})

        if user:
            criteria.append({'director': user['userId']})

        shifts = Shift.col.find({'$and': criteria}).sort('start_date')

        return [Shift.safe(s) for s in shifts]
    
    @staticmethod
    def delete(id):
        Shift.col.delete_one({'_id': ObjectId(id)})
