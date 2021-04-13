import json
from flask import Response, request, url_for
from nearbyEvents.constants import *
from nearbyEvents.models import *

# This code is based on the PWP course example of University of Oulu

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


class NearbyEventsBuilder(MasonBuilder):

    def add_control_delete_area(self, area):
        self.add_control(
            "nearby:delete",
            url_for("api.areaitem", area=area),
            method="DELETE",
            title="Delete this area"
        )

    def add_control_add_area(self):
        self.add_control(
            "nearby:add-area",
            url_for("api.areacollection"),
            method="POST",
            encoding="json",
            title="Add a new area",
            schema=Area.get_schema()
        )

    def add_control_add_event(self):
        self.add_control(
            "nearby:add-event",
            url_for("api.eventcollection"),
            method="POST",
            encoding="json",
            title="Add a new event",
            schema=Event.get_schema()
        )

    # def add_control_modify_sensor(self, sensor):
        # self.add_control(
            # "edit",
            # url_for("api.sensoritem", sensor=sensor),
            # method="PUT",
            # encoding="json",
            # title="Edit this sensor",
            # schema=Sensor.get_schema()
        # )

    def add_control_get_areas(self, area):
        base_uri = url_for("api.areacollection", area=area)
        uri = base_uri + "?start={index}"
        self.add_control(
            "nearby:areas-collection",
            uri,
            isHrefTemplate=True,
            schema=self._paginator_schema()
        )

    @staticmethod
    def _paginator_schema():
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        props = schema["properties"]
        props["index"] = {
            "description": "Starting index for pagination",
            "type": "integer",
            "default": "0"
        }
        return schema

def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)