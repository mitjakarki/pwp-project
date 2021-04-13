import json
from jsonschema import validate, ValidationError
from flask import request, Response, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from nearbyEvents.models import Area
from nearbyEvents import db
from nearbyEvents.utils import NearbyEventsBuilder, create_error_response
from nearbyEvents.constants import *

class AreaItem(Resource):

    def get(self, area):
        db_area = Area.query.filter_by(name=area).first()
        if db_area is None:
            return create_error_response(404, "Not found", 
                "No area was found with the name {}".format(area)
            )
        
        body = NearbyEventsBuilder(
            name=db_area.name
        )
        body.add_namespace("nearby", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.areaitem", area=area))
        body.add_control("profile", AREA_PROFILE)
        body.add_control("collection", url_for("api.areacollection"))
        body.add_control_delete_area(area)
        # body.add_control("nearby:areas-collection",
            # url_for("api.areacollection")
        # )
        
        return Response(json.dumps(body), 200, mimetype=MASON)
        
    def put(self, area):
        db_area = Area.query.filter_by(name=area).first()
        if db_area is None:
            return create_error_response(404, "Not found", 
                "No area was found with the name {}".format(area)
            )
        
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Area.get_schema())
        except ValidationError as e:
            db.session.rollback()
            return create_error_response(400, "Invalid JSON document", str(e))
    
        db_area.name = request.json["name"]
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(409, "Already exists", 
                "Area with name '{}' already exists.".format(request.json["name"])
            )
        
        return Response(status=204)

    def delete(self, area):
        db_area = Area.query.filter_by(name=area).first()
        if db_area is None:
            return create_error_response(404, "Not found", 
                "No area was found with the name {}".format(area)
            )
        
        db.session.delete(db_area)
        db.session.commit()
        
        return Response(status=204)
    


class AreaCollection(Resource):

    def get(self):
        body = NearbyEventsBuilder()

        body.add_namespace("nearby", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.areacollection"))
        body.add_control_add_area()
        body["items"] = []
        for db_area in Area.query.all():
            item = NearbyEventsBuilder(
                name=db_area.name
            )
            item.add_control("self", url_for("api.areaitem", area=db_area.name))
            item.add_control("profile", AREA_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)
        
    def post(self):
        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Area.get_schema())
        except ValidationError as e:
            db.session.rollback()
            return create_error_response(400, "Invalid JSON document", str(e))

        area = Area(
            name=request.json["name"]
        )

        try:
            db.session.add(area)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409, "Already exists",
                "Area with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=201, headers={
            "Location": url_for("api.areaitem", area=request.json["name"])
        })