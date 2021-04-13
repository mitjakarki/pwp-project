import os
import sys
import pytest
import tempfile
import json
import time
from datetime import datetime
import datetime
from jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError
o_path = os.getcwd()
sys.path.append(o_path)

import nearbyEvents.models
from nearbyEvents import app, db
from nearbyEvents.models import User, Event, Area, Country, Reservation, Ticket

# based on http://flask.pocoo.org/docs/1.0/testing/
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    }
    global app
    app = nearbyEvents.create_app(config)

    #db.create_all()
    with app.app_context():
        nearbyEvents.models.db.create_all()
        _populate_db()
    
    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _populate_db():
    country = Country(
        country="Finland",
        currency="EUR"
    )
    db.session.add(country)
    for i in range(1, 4):
        s = Area(
            name="test-area-{}".format(i)
        )
        e = Event(
            name="test-event-{}".format(i),
            max_tickets=150,
            ticket_price=19,
            status="Cancelled",
            event_begin=datetime.datetime.now() + datetime.timedelta(days = 1)
        )
        e.in_area=s
        db.session.add(s)
    db.session.commit()

def _get_area_json(number=1):
    return {"name": "extra-area-{}".format(number)}
    
def _get_event_json(number=1):
    return {"name": "extra-event-{}".format(number),
    "max_tickets": 2,
    "max_tickets": 2,
    "ticket_price": 50,
    "status": "Cancelled",
    "event_begin": "2018.2.2",
    "area_name": "test-area-3"}

def _check_control_get_method(ctrl, client, obj):

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200
    
def _check_control_delete_method(ctrl, client, obj):

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204

def _check_control_post_method(ctrl, client, obj):
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = _get_area_json()
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201
    
def _check_control_put_method(ctrl, client, obj):
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = _get_area_json()
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201
    
def _check_namespace(client, response):
    ns_href = response["@namespaces"]["nearby"]["name"]
    resp = client.get(ns_href)
    assert resp.status_code == 200

class TestAreaCollection(object):

    RESOURCE_URL = "/api/areas/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 3
        _check_namespace(client, body)
        for item in body["items"]:
            assert "name" in item
            _check_control_get_method("self", client, item)
            _check_namespace(client, body)
        _check_control_get_method("self", client, body)
               
    def test_post_valid_request(self, client):
        valid = _get_area_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "extra-area-1"
        
    def test_post_wrong_mediatype(self, client):
        valid = _get_area_json()
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
    def test_post_missing_field(self, client):
        valid = _get_area_json()
        valid['wrong_name'] = valid.pop('name')
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
    def test_post_valid_request_duplicate(self, client):
        valid = _get_area_json()
        valid["name"] = "test-area-1"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
class TestAreaItem(object):

    RESOURCE_URL = "/api/areas/test-area-1/"
    INVALID_URL = "/api/areas/non-area-x/"

    def test_put_wrong_mediatype(self, client):
        valid = _get_area_json()
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
    def test_put_missing(self, client):
        valid = _get_area_json()
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
    def test_put_valid(self, client):
        valid = _get_area_json()
        valid["name"] = "test-area-modified"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        
    def test_delete_valid(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404
        
    def test_delete_missing(self, client):
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
        
        
class TestEventCollection(object):

    RESOURCE_URL = "/api/events/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "name" in item
            _check_control_get_method("self", client, item)
        _check_control_get_method("self", client, body)
               
    def test_post_valid_request(self, client):
        valid = _get_event_json()
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "extra-event-1"
        
    def test_post_wrong_mediatype(self, client):
        valid = _get_event_json()
        resp = client.post(self.RESOURCE_URL, data="")
        assert resp.status_code == 415
        
    def test_post_missing_field(self, client):
        valid = _get_event_json()
        valid['wrong_name'] = valid.pop('name')
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
    def test_post_valid_request_duplicate(self, client):
        valid = _get_event_json()
        valid["name"] = "test-event-1"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
class TestEventItem(object):

    RESOURCE_URL = "/api/events/test-event-1/"
    INVALID_URL = "/api/event/non-event-x/"

    def test_put_wrong_mediatype(self, client):
        valid = _get_event_json()
        resp = client.put(self.RESOURCE_URL, data="")
        assert resp.status_code == 415
        
    def test_put_missing(self, client):
        valid = _get_event_json()
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
    def test_put_valid(self, client):
        valid = _get_event_json()
        valid["name"] = "test-event-modified"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        
        valid = _get_event_json()
    # remove field for 400
        valid.pop("area_name")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
    def test_delete_valid(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404
        
    def test_delete_missing(self, client):
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404