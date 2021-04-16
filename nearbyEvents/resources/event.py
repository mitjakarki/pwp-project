import json
from jsonschema import validate, ValidationError
from flask import request, Response, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from nearbyEvents.models import Area, Event
from nearbyEvents import db
from nearbyEvents.utils import NearbyEventsBuilder, create_error_response
from nearbyEvents.constants import *

class EventItem(Resource):

    """
        Retrieve single event based on the event name (string)
    """
    
    def get(self, event):
        db_event = Event.query.filter_by(name=event).first()
        if db_event is None:
            return create_error_response(404, "Not found", 
                "No event was found with the name {}".format(event)
            )
        
        body = NearbyEventsBuilder(
            name=db_event.name
        )
        body.add_namespace("nearby", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.eventitem", event=event))
        body.add_control("profile", EVENT_PROFILE)
        body.add_control("collection", url_for("api.eventcollection"))
        body.add_control_delete_event(db_event.name)
        body.add_control_modify_event(db_event.name)
        if db_event.area_name is not None:
            body.add_control_get_area(db_event.area_name)
        
        return Response(json.dumps(body), 200, mimetype=MASON)
        
    """
        Modify an event based on the event name (string)
        Must be JSON and include the parameter: name
    """
    def put(self, event):
        db_event = Event.query.filter_by(name=event).first()
        if db_event is None:
            return create_error_response(404, "Not found", 
                "No event was found with the name {}".format(event)
            )
        
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Event.get_schema())
        except ValidationError as e:
            db.session.rollback()
            return create_error_response(400, "Invalid JSON document", str(e))
    
        db_event.name = request.json["name"]
        db_event.status = request.json["status"]
        db_event.event_begin = request.json["event_begin"]
        db_event.area_name = request.json["area_name"]
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(409, "Already exists", 
                "Event with name '{}' already exists.".format(request.json["name"])
            )
        
        return Response(status=204)
    
    """
        Delete single event based on the event name (string)
    """
    def delete(self, event):
        db_event = Event.query.filter_by(name=event).first()
        if db_event is None:
            return create_error_response(404, "Not found", 
                "No event was found with the name {}".format(event)
            )
        
        db.session.delete(db_event)
        db.session.commit()
        
        return Response(status=204)
    

class EventCollection(Resource):

    """
        Retrieve all events in the system
    """
    def get(self):
        body = NearbyEventsBuilder()

        body.add_namespace("nearby", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.eventcollection"))
        body.add_control_add_event()
        body["items"] = []
        for db_event in Event.query.all():
            item = NearbyEventsBuilder(
                name=db_event.name
            )
            item.add_control("self", url_for("api.eventitem", event=db_event.name))
            item.add_control("profile", EVENT_PROFILE)
            if (db_event.area_name != None):
                item.add_control_get_area(db_event.area_name)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)
        
    """
        Add a new event to the system
        Must be JSON and uses name (string) as the parameter
    """
    def post(self):
        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Event.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        
        db_area = Area.query.filter_by(name=request.json["area_name"]).first()
        event = Event(
            name=request.json["name"],
            max_tickets=request.json["max_tickets"],
            ticket_price=request.json["ticket_price"],
            status=request.json["status"],
            event_begin=request.json["event_begin"]
        )
        event.in_area=db_area
        try:
            db.session.add(event)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            return create_error_response(
                409, "Already exists",
                "Event with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=201, headers={
            "Location": url_for("api.eventitem", event=request.json["name"])
        })