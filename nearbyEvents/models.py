import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
from nearbyEvents import db
import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(64), nullable=False, unique=True)
    nationality = db.Column(db.String(32), db.ForeignKey("country.country" , ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    
    reservations =  db.relationship("Reservation", back_populates="user_booked", cascade="all, delete-orphan")
    country = db.relationship("Country", back_populates="users")
    managed_events = db.relationship("Event", back_populates="is_managed_by")

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    max_tickets = db.Column(db.Integer, nullable=False)
    ticket_price = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(16), nullable=False)
    event_begin = db.Column(db.DateTime, nullable=False)
    event_manager = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    area_name = db.Column(db.String(64), db.ForeignKey("area.name", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    
    reservations =  db.relationship("Reservation", back_populates="for_event", cascade="all, delete-orphan")
    is_managed_by = db.relationship("User", back_populates="managed_events", foreign_keys=[event_manager])
    in_area = db.relationship("Area", back_populates="events")

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["name", "status", "event_begin", "area_name"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Event's unique name",
            "type": "string"
        }
        props["status"] = {
            "description": "Event's status",
            "type": "string"
        }
        props["event_begin"] = {
            "description": "Date for the happening",
            "type": "string",
            "pattern": "^[0-9]{4}-[01][0-9]-[0-3][0-9]T[0-9]{2}:[0-5][0-9]:[0-5][0-9]Z$"
        }
        props["area_name"] = {
            "description": "Name of the area",
            "type": "string"
        }
        return schema
        
class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    name = db.Column(db.String(64), nullable=False, unique=True)
    country = db.Column(db.String(32), db.ForeignKey("country.country", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, default="Finland")
    
    events = db.relationship("Event", back_populates="in_area")
    in_country = db.relationship("Country", back_populates="areas")
    
    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["name"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Area name",
            "type": "string"
        }
        return schema

    
class Country(db.Model):
    country = db.Column(db.String(32), primary_key=True)    
    timezone = db.Column(db.DateTime, nullable=True)
    currency = db.Column(db.String(3), nullable=True)
    
    users = db.relationship("User", back_populates="country")
    areas = db.relationship("Area", back_populates="in_country", cascade="all, delete-orphan")
    
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    paid = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    
    user_booked = db.relationship("User", back_populates="reservations")
    for_event = db.relationship("Event", back_populates="reservations")
    tickets = db.relationship("Ticket", back_populates="in_reservation", cascade="all, delete-orphan")

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservation.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    type = db.Column(db.String(16), nullable=True)
    
    in_reservation = db.relationship("Reservation", back_populates="tickets")
    
    
@click.command("initializeDatabase")
@with_appcontext
def initializeDatabase():
    db.create_all()

@click.command("generateTestDatabase")
@with_appcontext
def generateTestDatabase():
    user = User(
        first_name="user",
        last_name="test",
        birth_date=datetime.datetime.now(),
        email="user.test@gmail.com"
        )
    country = Country(
        country="Finland",
        currency="EUR"
        )  
    area = Area(
        name="Oulu - Keskusta"
    )
    event = Event(
        name="Stand Up Comedy at 45 Special",
        max_tickets=150,
        ticket_price=19,
        status="Cancelled",
        event_begin=datetime.datetime.now() + datetime.timedelta(days = 1)
    )
    reservation = Reservation(
        paid=True,
        created_at=datetime.datetime.now()
    )
    ticket = Ticket(
        type="VIP"
    )
    # Create relations
    area.in_country = country
    event.in_area = area
    event.is_managed_by = user
    reservation.for_event = event
    reservation.user_booked = user
    ticket.in_reservation = reservation
    
    # Populate database with test data
    db.session.add(ticket)
    db.session.commit()
