#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from jsonschema import validate, ValidationError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError


app = Flask(__name__, static_folder="static")
api = Api(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# constants
MASON                       = "application/vnd.mason+json"
# TODO are these correct?
EVENT_PROFILE               = "/profiles/event/"
EVENT_COLLECTION_PROFILE    = "/profiles/events/"
AREA_PROFILE                = "/profiles/area/"
AREA_COLLECTION_PROFILE     = "/profiles/areas/"

ERROR_PROFILE = "/profiles/error/"
LINK_RELATIONS_URL = "/storage/link-relations/"

class StorageEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    location = db.Column(db.String(64), nullable=False)

    product = db.relationship("Product", back_populates="in_storage")

class Event(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    max_tickets = db.Column(db.Integer, nullable=False)
    ticket_price = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(16), nullable=False)
    event_start = db.Column(db.DateTime, nullable=False)
    event_manager = db.Column(db.Integer, nullable=True)
    area_name = db.Column(db.String(64), nullable=True)

    # TODO define relationships
    in_storage = db.relationship("StorageEntry", back_populates="product")

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["id", "name", "max_tickets", "status", "event_start"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Event's unique name",
            "type": "string"
        }
        props["max_tickets"] = {
            "description": "Total amount of tickets to event",
            "type": "number"
        }
        props["ticket_price"] = {
            "description": "Ticket's price",
            "type": "number"
        }
        props["status"] = {
            "description": "Event status",
            "type": "string"
        }
        props["event_start"] = {
            "description": "Date and time of event",
            "type": "datetime"
        }
        props["event_manager"] = {
            "description": "Event creator's ID",
            "type": "number"
        }
        props["area_name"] = {
            "description": "Event location or area",
            "type": "string"
        }
        return schema

class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    handle = db.Column(db.String(64), unique=True, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)

    in_storage = db.relationship("StorageEntry", back_populates="product")

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["handle", "weight", "price"]
        }
        props = schema["properties"] = {}
        props["handle"] = {
            "description": "Product's unique name",
            "type": "string"
        }
        props["weight"] = {
            "description": "Product's weight",
            "type": "number"
        }
        props["price"] = {
            "description": "Product's price",
            "type": "number"
        }
        return schema

### utils
def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)


##########################################
############ EVENT CLASSES ###############
##########################################
class EventCollection(Resource):

    def get(self):
        body = InventoryBuilder()
        body.add_namespace("storage", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ProductCollection))
        body.add_control_add_product()
        body["items"] = []
        joined = Product.query.all()


        for i in joined:
            item = InventoryBuilder(
            handle=i.handle,
            weight=i.weight,
            price=i.price
            )
            item.add_control("self", api.url_for(ProductItem, handle=i.handle))
            item.add_control("profile", PRODUCT_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Product.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        product = Product(
            handle=request.json["handle"],
            weight=request.json["weight"],
            price=request.json["price"]
        )

        try:
            db.session.add(product)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Product with name '{}' already exists.".format(request.json["handle"])
            )

        return Response(status=201, headers={
            "Location": api.url_for(ProductItem, handle=request.json["handle"])
        })


class EventItem(Resource):

    def get(self, handle):
        prod = Product.query.filter_by(handle=handle).first()
        if prod is None:
            return create_error_response(404, "Not found", 
                "No product was found with the handle {}".format(handle)
            )

        body = InventoryBuilder(
            handle=prod.handle,
            weight=prod.weight,
            price=prod.price
        )
        body.add_namespace("storage", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ProductItem, handle=handle))
        body.add_control("profile", PRODUCT_PROFILE)
        body.add_control("collection", api.url_for(ProductCollection))
        body.add_control_edit_product(handle)
        body.add_control_delete_product(handle)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, handle):
        prod = Product.query.filter_by(handle=handle).first()
        if prod is None:
            return create_error_response(404, "Not found", 
                "No product was found with the handle {}".format(handle)
            )

        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Product.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        prod.handle = request.json["handle"]
        prod.weight = request.json["weight"]
        prod.price = request.json["price"]

        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Product with handle '{}' already exists.".format(request.json["handle"])
            )

        return Response(status=204)

    def delete(self, handle):
        prod = Product.query.filter_by(handle=handle).first()
        if prod is None:
            return create_error_response(404, "Not found", 
                "No product was found with the handle {}".format(handle)
            )
        
        db.session.delete(prod)
        db.session.commit()
        
        return Response(status=204)

##########################################
############ AREA CLASSES ################
##########################################
class AreaCollection(Resource):

    def get(self):
        body = InventoryBuilder()
        body.add_namespace("storage", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ProductCollection))
        body.add_control_add_product()
        body["items"] = []
        joined = Product.query.all()


        for i in joined:
            item = InventoryBuilder(
            handle=i.handle,
            weight=i.weight,
            price=i.price
            )
            item.add_control("self", api.url_for(ProductItem, handle=i.handle))
            item.add_control("profile", PRODUCT_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Product.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        product = Product(
            handle=request.json["handle"],
            weight=request.json["weight"],
            price=request.json["price"]
        )

        try:
            db.session.add(product)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Product with name '{}' already exists.".format(request.json["handle"])
            )

        return Response(status=201, headers={
            "Location": api.url_for(ProductItem, handle=request.json["handle"])
        })


class AreaItem(Resource):

    def get(self, handle):
        prod = Product.query.filter_by(handle=handle).first()
        if prod is None:
            return create_error_response(404, "Not found", 
                "No product was found with the handle {}".format(handle)
            )

        body = InventoryBuilder(
            handle=prod.handle,
            weight=prod.weight,
            price=prod.price
        )
        body.add_namespace("storage", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ProductItem, handle=handle))
        body.add_control("profile", PRODUCT_PROFILE)
        body.add_control("collection", api.url_for(ProductCollection))
        body.add_control_edit_product(handle)
        body.add_control_delete_product(handle)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, handle):
        prod = Product.query.filter_by(handle=handle).first()
        if prod is None:
            return create_error_response(404, "Not found", 
                "No product was found with the handle {}".format(handle)
            )

        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Product.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        prod.handle = request.json["handle"]
        prod.weight = request.json["weight"]
        prod.price = request.json["price"]

        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Product with handle '{}' already exists.".format(request.json["handle"])
            )

        return Response(status=204)

    def delete(self, handle):
        prod = Product.query.filter_by(handle=handle).first()
        if prod is None:
            return create_error_response(404, "Not found", 
                "No product was found with the handle {}".format(handle)
            )
        
        db.session.delete(prod)
        db.session.commit()
        
        return Response(status=204)

class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

class InventoryBuilder(MasonBuilder):

    @staticmethod
    def product_schema():
        schema = {
            "type": "object",
            "required": ["handle", "weight", "price"]
        }
        props = schema["properties"] = {}
        props["handle"] = {
            "description": "Product's unique name",
            "type": "string"
        }
        props["weight"] = {
            "description": "Product's weight",
            "type": "number"
        }
        props["price"] = {
            "description": "Product's price",
            "type": "number"
        }
        return schema

    def add_control_all_products(self):
        self.add_control(
            "storage:products-all",
            "/api/products/",
            method="GET",
            title="Go to list of all products"
        )

    def add_control_delete_product(self, product_handle):
        self.add_control(
            "storage:delete",
            href=api.url_for(ProductItem, handle=product_handle),
            handle=product_handle,
            method="DELETE",
            title="Delete this product"
        )

    def add_control_add_product(self):
        self.add_control(
            "storage:add-product",
            "/api/products/",
            method="POST",
            title="Add product",
            encoding="json",
            schema=self.product_schema()
        )

    def add_control_edit_product(self, product_handle):
        self.add_control(
            "edit",
            href=api.url_for(ProductItem, handle=product_handle),
            handle=product_handle,
            method="PUT",
            title="Edit product",
            encoding="json",
            schema=self.product_schema()
        )

@app.route("/api/")
def entry_point():
    body = InventoryBuilder(
        handle="asdasd",
        weight=666,
        price=667
    )
    body.add_namespace("storage", LINK_RELATIONS_URL)
    body.add_control_all_products()

    return Response(json.dumps(body), 200, mimetype=MASON)

api.add_resource(EventCollection, "/api/events/")
api.add_resource(EventItem, "/api/events/<handle>/")
api.add_resource(AreaCollection, "/api/areas/")
api.add_resource(AreaItem, "/api/areas/<handle>/")
api.add_resource(EventsByArea, "/api/areas/<area>/events/")

@app.route(LINK_RELATIONS_URL)
def send_link_relations():
    return "link relations"

@app.route("/profiles/<profile>/")
def send_profile(profile):
    return "you requested {} profile".format(profile)