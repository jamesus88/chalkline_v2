from chalkline.core import mailer, ObjectId
from pymongo import UpdateOne
from datetime import datetime
from chalkline.core.user import User

class Admin:

    @staticmethod
    def update_all(form, cls):
        updates = {}

        for key, value in form.items():
            if '_' not in key:
                continue

            _id, attr = key.split('_')

            # formatting
            date_attrs = ['date']
            int_attrs = ['field']
            multi_attrs = ['groups', 'permissions']

            if attr in date_attrs:
                value = datetime.strptime(value, "%Y-%m-%dT%H:%M")
            elif attr in int_attrs:
                value = int(value)
            elif attr in multi_attrs:
                value = form.getlist(key)

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
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, 'groups': {'$in': [f"{league['abbr']}.umpire"]}}, 
            {'$push': {'permissions': f"{league['abbr']}.umpire_add"}}
        )

    @staticmethod
    def umpire_add_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, 'groups': {'$in': [f"{league['abbr']}.umpire"]}}, 
            {'$pull': {'permissions': f"{league['abbr']}.umpire_add"}}
        )

    @staticmethod
    def umpire_remove_all(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, 'groups': {'$in': [f"{league['abbr']}.umpire"]}}, 
            {'$push': {'permissions': f"{league['abbr']}.umpire_remove"}}
        )

    @staticmethod
    def umpire_remove_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, 'groups': {'$in': [f"{league['abbr']}.umpire"]}}, 
            {'$pull': {'permissions': f"{league['abbr']}.umpire_remove"}}
        )
    
    @staticmethod
    def coach_add_all(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, 'groups': {'$in': [f"{league['abbr']}.coach"]}}, 
            {'$push': {'permissions': f"{league['abbr']}.coach_add"}}
        )

    @staticmethod
    def coach_add_none(league):
        User.col.update_many(
            {'active': True, 'leagues': {'$in': [league['leagueId']]}, 'groups': {'$in': [f"{league['abbr']}.coach"]}}, 
            {'$pull': {'permissions': f"{league['abbr']}.coach_add"}}
        )


            
