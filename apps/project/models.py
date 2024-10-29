"""
This file defines the database models
"""

import datetime, csv, json
from .common import db, Field, auth
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later

# Species table
db.define_table('species',
    Field('name', 'string', requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'species.name')]),
)

# Checklist table
db.define_table('checklist',
    Field('event_id', 'string', unique=True),
    Field('location', 'json', requires=IS_NOT_EMPTY()),
    Field('created_on', 'datetime', default=get_time),
    Field('user_id', default=get_user_email),
    Field('content', 'json', default={}),
    Field('name', 'string', default='Untitled Checklist')
)

# Sightings table
db.define_table('sighting',
    Field('event_id', 'string', requires=[IS_NOT_EMPTY(), IS_IN_DB(db, 'checklist.event_id', '%(event_id)s')]),
    Field('species_id', 'reference species', requires=IS_IN_DB(db, 'species.id', '%(name)s')),
    Field('number_seen', 'integer', default=1, requires=IS_INT_IN_RANGE(1, None)),
    Field('user_id', 'string', default=get_user_email)
    
)

names_to_id = {}

if db(db.species).isempty():
    with open("apps/project/species.csv") as f:
        csv_reader = csv.reader(f)
        next(csv_reader) # Skip the header
        for row in csv_reader:
            id = db.species.insert(name=row[0])
            names_to_id[row[0]] = id

if db(db.checklist).isempty():
    with open("apps/project/checklists.csv") as f:
        csv_reader = csv.reader(f)
        next(csv_reader) # Skip the header
        for row in csv_reader:
            if row[4] == '':
                row[4] = '00:00:00'
            db.checklist.insert(
                event_id=row[0],
                location= json.dumps({'latitude': row[1], 'longitude': row[2]}),
                created_on= datetime.datetime.strptime(f"{row[3]} {row[4]}", '%Y-%m-%d %H:%M:%S'),
                user_id= row[5],
            )
            
if db(db.sighting).isempty():
    with open("apps/project/sightings.csv") as f:
        csv_reader = csv.reader(f)
        next(csv_reader) # Skip the header
        for row in csv_reader:
            if row[2] == 'X':
                row[2] = 0
            db.sighting.insert(
                event_id=row[0],
                species_id=names_to_id[row[1]],
                number_seen=row[2],
            )


db.commit()