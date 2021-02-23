import os
import sys
import pytest
import tempfile
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
o_path = os.getcwd()
sys.path.append(o_path)

#from nearbyEvents import db
import nearbyEvents.models
from nearbyEvents import app
#from nearbyEvents import db
from nearbyEvents.models import User, Event, Area, Country, Reservation, Ticket
import datetime
#db = SQLAlchemy()
#This code is based on https://flask.palletsprojects.com/en/1.0.x/testing/
#config = {
##        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
#        "TESTING": True,
#        "SQLALCHEMY_TRACK_MODIFICATIONS": False
#    }
#app = nearbyEvents.create_app(config)
@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    }
    global app
    app = nearbyEvents.create_app(config)
    #config = {
    #    "SQLALCHEMY_DATABASE_URI": "sqlite:///test.db",
    #    "TESTING": True,
    #    "SQLALCHEMY_TRACK_MODIFICATIONS": False
    #}
    #app = nearbyEvents.create_app(config)
    #nearbyEvents.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    #app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    #nearbyEvents.app.config["TESTING"] = True
    #nearbyEvents.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    #app.db.init_app(app)
    #nearbyEvents.db.init_app(nearbyEvents.app)
    #db = SQLAlchemy(app)
    #db.create_all()
    #initializeDatabase()
    #db.init_app(app)
    from nearbyEvents.models import User, Event, Area, Country, Reservation, Ticket
    with app.app_context():
        nearbyEvents.models.db.init_app(app)
        nearbyEvents.models.db.create_all()
        
    yield nearbyEvents.models.db
    
    nearbyEvents.models.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

from sqlalchemy.engine import Engine
from sqlalchemy import event
from nearbyEvents.models import User, Event, Area, Country, Reservation, Ticket

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def _get_user():
    """Creates a dummy User instance"""
    return User(
        first_name="user",
        last_name="test",
        birth_date=datetime.datetime.now(),
        email="user.test@gmail.com"
        
    )
    
def _get_Country():
    """Creates a dummy Country instance"""
    return Country(
        country="Finland",
        currency="EUR"
    )
    
def _get_Area():
    """Creates a dummy Area instance"""
    return Area(
        name="Oulu - Keskusta"
    )
    
def _get_Event():
    """Creates a dummy Event instance"""
    return Event(
        name="Stand Up Comedy at 45 Special",
        max_tickets=150,
        ticket_price=19,
        status="Cancelled",
        event_begin=datetime.datetime.now() + datetime.timedelta(days = 1)
    )
def _get_Reservation():
    """Creates a dummy Reservation instance"""
    return Reservation(
        paid=True,
        created_at=datetime.datetime.now()
    )
    
def _get_Ticket():
    """Creates a dummy Ticket instance"""
    return Ticket(
        type="VIP"
    )
    
def test_create_instances(db_handle):
    """
    Tests that we can create one instance of each model and save them to the
    database using valid values for all columns. After creation, test that 
    everything can be found from database, and that all relationships have been
    saved correctly.
    """
    with app.app_context():
        # Create everything
        user = _get_user()
        country=_get_Country()
        event=_get_Event()
        area=_get_Area()
        reservation=_get_Reservation()
        ticket=_get_Ticket()
        
        area.in_country=country
        user.country=country
        event.in_area=area
        event.is_managed_by=user
        ticket.in_reservation=reservation
        reservation.user_booked=user
        reservation.for_event=event
        
        db_handle.session.add(user)
        db_handle.session.add(country)
        db_handle.session.add(area)
        db_handle.session.add(event)
        db_handle.session.add(reservation)
        db_handle.session.add(ticket)
        db_handle.session.commit()
        
        # Check that everything exists
        assert User.query.count() == 1
        assert Country.query.count() == 1
        assert Area.query.count() == 1
        assert Event.query.count() == 1
        assert Reservation.query.count() == 1
        assert Ticket.query.count() == 1
        db_user = User.query.first()
        db_country = Country.query.first()
        db_area = Area.query.first()
        db_event = Event.query.first()
        db_reservation = Reservation.query.first()
        db_ticket = Ticket.query.first()
        
        # Check all relationships (both sides)
        assert db_user.country == db_country
        assert db_user in db_country.users
        
        assert db_area.in_country == db_country
        
        assert db_event in db_user.managed_events
        assert db_event.is_managed_by == db_user
        assert db_event.in_area == db_area
        assert db_event in db_area.events
        
        assert db_reservation in db_event.reservations
        assert db_reservation in db_user.reservations
        assert db_reservation.user_booked == db_user
        assert db_reservation.for_event == db_event
        
        assert db_ticket.in_reservation == db_reservation
        assert db_ticket in db_reservation.tickets

def test_user_ondelete_country(db_handle):
    """
    Tests that users's nationality foreign key is set to null when the country
    is deleted.
    """
    with app.app_context():
        # Create instances
        user = _get_user()
        country = _get_Country()
        
        # Create relations
        user.country = country
        
        # Add to database and then delete the relation instance
        db_handle.session.add(user)
        db_handle.session.commit()
        db_handle.session.delete(country)
        db_handle.session.commit()
        
        # See if the ondelete function works as designed
        assert user.nationality is None
    
def test_area_ondelete_country(db_handle):
    """
    Tests that row of the area is deleted when the country
    is deleted.
    """
    with app.app_context():
        # Create instances
        area = _get_Area()
        country = _get_Country()
        
        # Create relations
        area.in_country = country
        # Add to database and then delete the relation instance
        db_handle.session.add(area)
        db_handle.session.commit()
        db_handle.session.delete(country)
        db_handle.session.commit()
        
        # See if the ondelete function works as designed
        assert Area.query.count() == 0
    
def test_event_ondelete_manager(db_handle):
    """
    Tests that the manager is null when the manager
    is deleted.
    """
    with app.app_context():
        # Create instances
        user = _get_user()
        event = _get_Event()
        
        # Create relations
        event.is_managed_by = user
        
        # Add to database
        db_handle.session.add(event)
        db_handle.session.commit()
        
        # See if the relation was correct
        assert event.event_manager == user.id
        
        # delete the relation instance
        db_handle.session.delete(user)
        db_handle.session.commit()
        # See if the ondelete function works as designed
        assert event.event_manager is None
def test_event_ondelete_area(db_handle):
    """
    Tests that the in_area is null when the area
    is deleted.
    """
    with app.app_context():
        # Create instances
        area = _get_Area()
        country = _get_Country()
        event = _get_Event()
        # Create relations
        event.in_area = area
        area.in_country = country
        
        # Add to database
        db_handle.session.add(area)
        db_handle.session.commit()
        
        # See if the relation was correct
        assert event.area_name == area.name
        
        # delete the relation instance
        db_handle.session.delete(area)
        db_handle.session.commit()
        
        # See if the ondelete function works as designed
        assert event.area_name is None

def test_reservation_ondelete_user(db_handle):
    """
    Tests that row of the reservation is deleted when the user
    is deleted.
    """
    with app.app_context():
        # Create instances
        reservation = _get_Reservation()
        area = _get_Area()
        country = _get_Country()
        event = _get_Event()
        user = _get_user()
        
        # Create relations
        area.in_country = country
        event.in_area = area
        reservation.for_event = event
        reservation.user_booked = user
        
        # Add to database and then delete the relation instance
        db_handle.session.add(reservation)
        db_handle.session.commit()
        db_handle.session.delete(user)
        db_handle.session.commit()
        
        # See if the ondelete function works as designed
        assert Reservation.query.count() == 0
    
def test_reservation_ondelete_event(db_handle):
    """
    Tests that row of the reservation is deleted when the event
    is deleted.
    """
    with app.app_context():
        # Create instances
        reservation = _get_Reservation()
        area = _get_Area()
        country = _get_Country()
        event = _get_Event()
        user = _get_user()
        
        # Create relations
        area.in_country = country
        event.in_area = area
        reservation.for_event = event
        reservation.user_booked = user
        
        # Add to database and then delete the relation instance
        db_handle.session.add(reservation)
        db_handle.session.commit()
        db_handle.session.delete(event)
        db_handle.session.commit()
        
        # See if the ondelete function works as designed
        assert Reservation.query.count() == 0
    
def test_ticket_ondelete_reservation(db_handle):
    """
    Tests that row of the ticket is deleted when the reservation
    is deleted.
    """
    with app.app_context():
        # Create instances
        reservation = _get_Reservation()
        area = _get_Area()
        country = _get_Country()
        event = _get_Event()
        user = _get_user()
        ticket = _get_Ticket()
        
        # Create relations
        area.in_country = country
        event.in_area = area
        reservation.for_event = event
        reservation.user_booked = user
        ticket.in_reservation = reservation
        
        # Add to database and then delete the relation instance
        db_handle.session.add(ticket)
        db_handle.session.commit()
        db_handle.session.delete(reservation)
        db_handle.session.commit()
        
        # See if the ondelete function works as designed
        assert Ticket.query.count() == 0