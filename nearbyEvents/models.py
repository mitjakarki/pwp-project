import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy()


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    status = db.Column(db.String(16), nullable=False)
    event_begin = db.Column(db.DateTime, nullable=False)
    area_name = db.Column(db.String(64), db.ForeignKey("area.name", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    
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
        props = schema["properties"] = {}
        props["status"] = {
            "description": "Event's status",
            "type": "string"
        }
        props["event_begin"] = {
            "description": "Date for the happening",
            "type": "datetime"
        }
        props["area_name"] = {
            "description": "Name of the area",
            "type": "string"
        }
        return schema
    
class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)    
    name = db.Column(db.String(64), nullable=False, unique=True)

    events = db.relationship("Event", back_populates="in_area")

    
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
    
    
@click.command("initializeDatabase")
@with_appcontext
def initializeDatabase():
    db.create_all()

@click.command("generateTestDatabase")
@with_appcontext
def generateTestDatabase():
    area = Area(
        name="Oulu - Keskusta"
    )
    event = Event(
        name="Stand Up Comedy at 45 Special",
        status="Cancelled",
        event_begin=datetime.datetime.now() + datetime.timedelta(days = 1)
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
