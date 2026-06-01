from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user') # 'admin' or 'user'
    profile_picture = db.Column(db.String(255), nullable=True, default='default_profile.png')
    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False) # e.g., 'Deluxe', 'Suite'
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, default=4)
    amenities = db.Column(db.String(255), default="Free WiFi, Air Conditioning, Smart TV")
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    bookings = db.relationship('Booking', backref='room', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    guest_count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Pending') # 'Pending', 'Approved', 'Rejected', 'Cancelled', 'Unpaid', 'Awaiting Approval', 'Checked-in', 'Completed'
    total_price = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 to 5
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
