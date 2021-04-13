  
from flask import Blueprint
from flask_restful import Api

from nearbyEvents.resources.area import AreaCollection, AreaItem
from nearbyEvents.resources.event import EventCollection, EventItem

#from nearbyEvents.resources.location import LocationItem, LocationSensorPairing
#from nearbyEvents.resources.measurement import MeasurementCollection

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(AreaCollection, "/areas/")
api.add_resource(AreaItem, "/area/<area>/")
api.add_resource(EventCollection, "/events/")
api.add_resource(EventItem, "/events/<event>/")
#api.add_resource(LocationItem, "/locations/<location>/")
#api.add_resource(MeasurementCollection, "/sensors/<sensor>/measurements/")
#api.add_resource(LocationSensorPairing, "/locations/<location>/<sensor>/")