import json
from jsonschema import validate, ValidationError
from flask import request, Response, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from nearbyEvents.models import Area
from nearbyEvents import db
from nearbyEvents.utils import NearbyEventsBuilder, create_error_response
from nearbyEvents.constants import *

class EventItem(Resource):

    def get(self, event):
        db_area = Event.query.filter_by(name=event).first()
        if db_area is None:
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
        body.add_control_delete_event(event)
        # body.add_control("nearby:events-collection",
            # url_for("api.eventcollection")
        # )
        
        return Response(json.dumps(body), 200, mimetype=MASON)


class EventCollection(Resource):

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
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)
        
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

        event = Event(
            name=request.json["name"]
            status=request.json["status"],
            event_begin=request.json["event_begin"],
            area_name=request.json["area_name"]
        )

        try:
            db.session.add(event)
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Event with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=201, headers={
            "Location": url_for("api.eventitem", event=request.json["name"])
        })