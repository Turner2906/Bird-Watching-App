"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email
from py4web.utils.form import Form, FormStyleBulma
from py4web.utils.grid import Grid, GridClassStyleBulma, Column
from .helpers import GridActionButton
from pydal.validators import IS_NOT_EMPTY
import json


url_signer = URLSigner(session)

@action('index')
@action.uses('index.html', db, auth, url_signer)
def index():
    return dict(
        # COMPLETE: return here any signed URLs you need.
        my_callback_url = URL('my_callback', signer=url_signer),
        get_species_coordinates_url = URL('get_species_coordinates', signer=url_signer),
        get_all_species_coordinates_url = URL('get_all_species_coordinates', signer=url_signer),
        get_species_url = URL('get_species', signer=url_signer),
    )
@action('stats')
@action.uses('stats.html', db, auth, url_signer)
def statistics():
    return dict(
        load_data_url = URL('load_data', signer=url_signer),
    )

@action('checklist/<checklist_id>')
@action.uses('checklist.html', db, auth, url_signer)
def checklist(checklist_id):
    logged_in = "True"
    if not auth.get_user():
        logged_in = "False"
    return dict(
        my_callback_url = URL('my_callback', signer=url_signer),
        load_data_url = URL('load_data', signer=url_signer),
        save_checklist_url = URL('save_checklist', signer=url_signer),
        update_checklist_url = URL('update_checklist', signer=url_signer),
        get_checklist_url = URL('get_checklist', signer=url_signer),
        checklist_id = checklist_id,
        logged_in = logged_in,
    )



@action('my_checklists/<path:path>', method=['POST','GET'])
@action('my_checklists', method=['POST','GET'])
@action.uses('my_checklists.html', db, auth, url_signer)
def my_checklists(path = None):
    columns = [
        db.checklist.name,
        db.checklist.event_id,
        db.checklist.created_on,
        ]
    post_action_buttons = [
        lambda row: GridActionButton(
            url = URL('checklist', row.event_id),
            text="Edit Checklist",
            icon="fa-pencil-square-o ",
            additional_classes="button confirmation is-small",
    )
    ]
    grid = Grid(path,
                formstyle= FormStyleBulma,
                grid_class_style=GridClassStyleBulma,
                columns=columns,
                query = (db.checklist.user_id == get_user_email),
                orderby = ~db.checklist.created_on,
                create=False,
                details=False,
                editable=False,
                pre_action_buttons=post_action_buttons,
                headings = ['Checklist Title', 'Checklist ID', 'Created On']
                )
    return dict(
            grid = grid,
            my_callback_url = URL('my_callback', signer=url_signer),
            load_data_url = URL('load_data', signer=url_signer),
            save_checklist_url = URL('save_checklist', signer=url_signer))

@action('load_data', method="GET")
@action.uses(db, auth)
def load_data():
    user_email = get_user_email()
    species_list = db(db.species).select().as_list()
    user_checklist_list = db(db.checklist.user_id == user_email).select().as_list()
    checklist_list = db(db.checklist).select().as_list()
    return dict(species=species_list, user_checklist_list=user_checklist_list, checklists=checklist_list)

@action('save_checklist', method="POST")
@action.uses(db, auth)
def save_checklist():
    id = db.checklist.insert(
        location = request.json.get('location'),
        content = request.json.get('checklist'),
        name = request.json.get('name')
    )
    cl = db(db.checklist.id == id).select().first()
    cl.update_record(event_id = str(id))
    return dict(id=id)

@action('update_checklist', method="POST")
@action.uses(db, auth)
def update_checklist():
    event_id = request.json.get('event_id')
    content = request.json.get('checklist')
    db(db.checklist.event_id == event_id).update(content = content, name = request.json.get('name'))
    return dict()

@action('get_checklist', method="POST")
@action.uses(db, auth)
def get_checklist():
    same_user = "True"
    event_id = request.json.get('event_id')
    checklist = db(db.checklist.event_id == event_id).select().first()
    if get_user_email() != checklist.user_id:
        same_user = "False"
    name = checklist.name
    return dict(checklist = checklist.content, name = name, date = checklist.created_on, location = checklist.location, same_user = same_user)

@action('my_callback')
@action.uses() # Add here things like db, auth, etc.
def my_callback():
    # The return value should be a dictionary that will be sent as JSON.
    return dict(my_value=3)

@action('location/<path:path>',method=['POST','GET'])
@action('location',method=['POST','GET'])
@action.uses('location.html',db,auth,url_signer)
def location(path=None):
    return dict(location_data = URL('location_data'))

@action('location_data',method=['GET','POST'])
@action.uses(db,auth)
def get_location_data():
    maxLat = request.json.get('maxlat')
    minLat = request.json.get('minlat')

    maxLng = request.json.get('maxlng')
    minLng = request.json.get('minlng')

    checklist_row = db(db.checklist).select(orderby=db.checklist.user_id)

    checklist_array = []
    sighting_array = []

    for r in checklist_row:
        location = json.loads(r.location)
        lat = float(location['latitude'])
        lng = float(location['longitude'])
        if lat >= minLat and lat <= maxLat and lng >= minLng and lng <= maxLng:
            sighting_obj = db(db.sighting.event_id == r.event_id).select().first()
            if sighting_obj != None: 
                species_obj = db(db.species.id == sighting_obj.species_id).select().first()
                sighting_obj['species_name'] = species_obj.name
                sighting_array.append(sighting_obj)
                checklist_array.append(r)

    return dict(checklist = checklist_array, sighting=sighting_array)

@action('get_species_coordinates', method=["GET"])
@action.uses(db)
def get_species_coordinates():
    species_name = request.params.get('species_name')
    rows = db((db.sighting.species_id == db.species.id) & 
              (db.sighting.event_id == db.checklist.event_id) &
              (db.species.name == species_name)).select(
                  db.checklist.location
              )
    coordinates = [json.loads(row.location) for row in rows]
    return dict(coordinates=coordinates)

@action('get_species', method='GET')
@action.uses(db)
def get_species():
    species = db(db.species).select().as_list()
    return dict(species=species)

@action('get_all_species_coordinates', method=["GET"])
@action.uses(db)
def get_all_species_coordinates():
    rows = db(db.checklist).select(db.checklist.location).as_list()
    coordinates = [json.loads(row['location']) for row in rows]
    return dict(coordinates=coordinates)


    
