import json
from jsonschema import validate, ValidationError
from flask import request, Response, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from nearbyEvents.models import Area, Event
from nearbyEvents import db
from nearbyEvents.utils import NearbyEventsBuilder, create_error_response
from nearbyEvents.constants import *

class EventsByArea(Resource):

    """
        Retrieve events that are in a given area. Requires area name (string)
    """
    def get(self, area):
        db_eventsbyarea = Event.query.filter(Event.area_name == area).all()
        if db_eventsbyarea is None:
            return create_error_response(404, "Not found", 
                "No area was found with the name {}".format(area)
            )
        body = NearbyEventsBuilder()

        body.add_namespace("nearby", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.eventsbyarea", area=area))
        body.add_control_get_areas()
        body["items"]=[]
        
        for db_event in db_eventsbyarea:
            #body.add_control_get_event(db_event.name)
            item = NearbyEventsBuilder(
                name=db_event.name
            )
            item.add_control("self", url_for("api.eventitem", event=db_event.name))
            item.add_control("profile", AREA_PROFILE)
            item.add_control_get_area(db_event.area_name)
            body["items"].append(item)
        
        return Response(json.dumps(body), 200, mimetype=MASON)