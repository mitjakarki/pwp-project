import os
import pytest
import tempfile

import app
import datetime

#This code is based on https://flask.palletsprojects.com/en/1.0.x/testing/

@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    app.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.app.config["TESTING"] = True
    
    with app.app.app_context():
        app.db.create_all()
        
    yield app.db
    
    app.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)
    
from app import User, Event, Area, Country, Reservation, Ticket
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def _get_user():
    return User(
        first_name="user",
        last_name="test",
        birth_date=datetime.datetime.now(),
        email="user.test@gmail.com"
        
    )
    
def _get_Country():
    return Country(
        country="Finland",
        currency="EUR"
    )
    
def _get_Area():
    return Area(
        name="Oulu - Keskusta"
    )
    
def _get_Event():
    return Event(
        name="Stand Up Comedy at 45 Special",
        max_tickets=150,
        ticket_price=19,
        status="Cancelled",
        event_begin=datetime.datetime.now() + datetime.timedelta(days = 1)
    )
def _get_Reservation():
    return Reservation(
        paid=True,
        created_at=datetime.datetime.now()
    )
    
def _get_Ticket():
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
    
    user = _get_user()
    country = _get_Country()
    user.country = country
    db_handle.session.add(user)
    db_handle.session.commit()
    db_handle.session.delete(country)
    db_handle.session.commit()
    assert user.nationality is None
    
def test_area_ondelete_country(db_handle):
    """
    Tests that row of the area is deleted when the country
    is deleted.
    """
    
    area = _get_Area()
    country = _get_Country()
    area.in_country = country
    db_handle.session.add(area)
    db_handle.session.commit()
    db_handle.session.delete(country)
    db_handle.session.commit()
    assert Area.query.count() == 0
    
def test_event_ondelete_manager(db_handle):
    """
    Tests that the manager is null when the manager
    is deleted.
    """
    
    user = _get_user()
    event = _get_Event()
    event.is_managed_by = user
    db_handle.session.add(event)
    db_handle.session.commit()
    assert event.event_manager == user.id
    db_handle.session.delete(user)
    db_handle.session.commit()
    assert event.event_manager is None
def test_event_ondelete_area(db_handle):
    """
    Tests that the in_area is null when the area
    is deleted.
    """
    
    area = _get_Area()
    country = _get_Country()
    event = _get_Event()
    event.in_area = area
    area.in_country = country
    db_handle.session.add(area)
    db_handle.session.commit()
    assert event.area_name == area.name
    db_handle.session.delete(area)
    db_handle.session.commit()
    assert event.area_name is None

def test_reservation_ondelete_user(db_handle):
    """
    Tests that row of the reservation is deleted when the user
    is deleted.
    """
    
    reservation = _get_Reservation()
    area = _get_Area()
    country = _get_Country()
    event = _get_Event()
    user = _get_user()
    
    area.in_country = country
    event.in_area = area
    reservation.for_event = event
    reservation.user_booked = user
    
    db_handle.session.add(reservation)
    db_handle.session.commit()
    db_handle.session.delete(user)
    db_handle.session.commit()
    assert Reservation.query.count() == 0
    
def test_reservation_ondelete_event(db_handle):
    """
    Tests that row of the reservation is deleted when the event
    is deleted.
    """
    
    reservation = _get_Reservation()
    area = _get_Area()
    country = _get_Country()
    event = _get_Event()
    user = _get_user()
    
    area.in_country = country
    event.in_area = area
    reservation.for_event = event
    reservation.user_booked = user
    
    db_handle.session.add(reservation)
    db_handle.session.commit()
    db_handle.session.delete(event)
    db_handle.session.commit()
    assert Reservation.query.count() == 0
    
def test_ticket_ondelete_reservation(db_handle):
    """
    Tests that row of the ticket is deleted when the reservation
    is deleted.
    """
    
    reservation = _get_Reservation()
    area = _get_Area()
    country = _get_Country()
    event = _get_Event()
    user = _get_user()
    ticket = _get_Ticket()
    
    area.in_country = country
    event.in_area = area
    reservation.for_event = event
    reservation.user_booked = user
    ticket.in_reservation = reservation
    
    db_handle.session.add(ticket)
    db_handle.session.commit()
    db_handle.session.delete(reservation)
    db_handle.session.commit()
    assert Ticket.query.count() == 0