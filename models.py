from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from app import app
from datetime import datetime

db = SQLAlchemy(app)

# -----------------------
# Property Owner
# -----------------------

class PropertyOwner(db.Model):
    __tablename__ = 'owner'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_code = db.Column(db.String(6), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False, unique=True)
    dob = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(300), nullable=False)
    id_type = db.Column(db.String(70), nullable=False)
    id_number = db.Column(db.String(50), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    status = db.Column(db.String(50), nullable=False, default='Active')  # e.g., Pending, Approved, Suspended
    profile_picture = db.Column(db.String(500), nullable=True)

    properties = db.relationship('PropertyInfo', back_populates='owner', cascade="all, delete-orphan")


# -----------------------
# User
# -----------------------

class UserInfo(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False, unique=True)
    dob = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(300), nullable=True)
    id_type = db.Column(db.String(70), nullable=True)
    id_number = db.Column(db.String(50), nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    status = db.Column(db.String(50), nullable=False, default='Active')  # e.g., Active, Suspended

    bookings = db.relationship('UserBooking', back_populates='user', cascade="all, delete-orphan")
    booking_history = db.relationship('BookingHistory', back_populates='user', cascade="all, delete-orphan")
    reviews = db.relationship('Review', back_populates='user', cascade="all, delete-orphan")


# -----------------------
# Admin
# -----------------------

class AdminInfo(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_code = db.Column(db.String(6), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False, unique=True)
    dob = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(300), nullable=True)
    id_type = db.Column(db.String(70), nullable=True)
    id_number = db.Column(db.String(50), nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())
    status = db.Column(db.String(50), nullable=False, default='Active')  # e.g., Active, Suspended
    
class AdminCode(db.Model):
    __tablename__ = 'admin_code'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), nullable=False, unique=True)  # unique code for new admin
    description = db.Column(db.String(200), nullable=True)         # optional description
    status = db.Column(db.String(20), nullable=False, default='Unused')  # 'Used' or 'Unused'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)  # assigned admin if code is used

    admin = db.relationship('AdminInfo', backref=db.backref('assigned_code', uselist=False))

# -----------------------
# Property
# -----------------------

class PropertyInfo(db.Model):
    __tablename__ = 'property'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prop_code = db.Column(db.String(6), nullable=False, unique=True)
    property_name = db.Column(db.String(200), nullable=False)
    property_type = db.Column(db.String(100), nullable=False)
    short_description = db.Column(db.String(500), nullable=False)
    guest_capacity = db.Column(db.Integer, nullable=False)
    bedroom_count = db.Column(db.Integer, nullable=False)
    bathroom_count = db.Column(db.Integer, nullable=False)
    property_size = db.Column(db.Float, nullable=False)  # Size in square feet or meters
    street_address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(200), nullable=False)
    state = db.Column(db.String(200), nullable=False)
    zip_code = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(200), nullable=False)
    full_description = db.Column(db.Text, nullable=True)
    amenities = db.Column(db.String(500), nullable=True)
    additional_amenities = db.Column(db.String(500), nullable=True)
    property_photos = db.Column(db.String(500), nullable=True)  # Comma-separated list of photo URLs
    nearby = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Pending')  # e.g., Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.now())

    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    owner = db.relationship('PropertyOwner', back_populates='properties')

    rooms = db.relationship('RoomInfo', back_populates='property', cascade="all, delete-orphan")
    bookings = db.relationship('UserBooking', back_populates='property', cascade="all, delete-orphan")
    booking_history = db.relationship('BookingHistory', back_populates='property', cascade="all, delete-orphan")
    reviews = db.relationship('Review', back_populates='property', cascade="all, delete-orphan")


# -----------------------
# Room
# -----------------------

class RoomInfo(db.Model):
    __tablename__ = 'room'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    no_of_rooms = db.Column(db.Integer, nullable=False, default=1)
    room_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    room_size = db.Column(db.Float, nullable=False)  # Size in square feet or meters
    bed_type = db.Column(db.String(100), nullable=False)
    amenities = db.Column(db.Text)
    image_url = db.Column(db.String(555))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    property = db.relationship('PropertyInfo', back_populates='rooms')

    bookings = db.relationship('UserBooking', back_populates='room', cascade="all, delete-orphan")
    booking_history = db.relationship('BookingHistory', back_populates='room', cascade="all, delete-orphan")


# -----------------------
# User Booking (Active)
# -----------------------

class UserBooking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_code = db.Column(db.String(6), nullable=False, unique=True)
    booking_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    end_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    status = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    user = db.relationship('UserInfo', back_populates='bookings')
    property = db.relationship('PropertyInfo', back_populates='bookings')
    room = db.relationship('RoomInfo', back_populates='bookings')
    review = db.relationship('Review', back_populates='booking', cascade="all, delete-orphan", uselist=False)



# -----------------------
# Booking History (Archived)
# -----------------------

class BookingHistory(db.Model):
    __tablename__ = 'booking_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_code = db.Column(db.String(6), nullable=False, unique=True)
    booking_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

    user = db.relationship('UserInfo', back_populates='booking_history')
    property = db.relationship('PropertyInfo', back_populates='booking_history')
    room = db.relationship('RoomInfo', back_populates='booking_history')


# -----------------------
# Review Table
# -----------------------

class Review(db.Model):
    __tablename__ = 'review'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    review_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)

    user = db.relationship('UserInfo', back_populates='reviews')
    property = db.relationship('PropertyInfo', back_populates='reviews')
    booking = db.relationship('UserBooking', back_populates='review')


class AdminNotification(db.Model):
    __tablename__ = 'admin_notification'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), default="info")  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    admin = db.relationship('AdminInfo', backref=db.backref('notifications', lazy=True))
    
# notification for user
class UserNotification(db.Model):
    __tablename__ = 'user_notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), default="info")  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('UserInfo', backref=db.backref('notifications', lazy=True))

class UserNotificationRead(db.Model):
    __tablename__ = "user_notification_read"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    notification_id = db.Column(db.Integer, db.ForeignKey("user_notification.id"), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("UserInfo", backref="read_notifications")
    notification = db.relationship("UserNotification", backref="read_by_users")
    
# owner notification
class OwnerNotification(db.Model):
    __tablename__ = 'owner_notification'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), default="info")  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    owner = db.relationship('PropertyOwner', backref=db.backref('notifications', lazy=True))
    
# contact and support table
class ContactSupport(db.Model):
    __tablename__ = 'contact_support'
    
    id = db.Column(db.Integer, primary_key=True)
    message_code = db.Column(db.String(6), nullable=False, unique=True)
    msg_from = db.Column(db.String(50), nullable=False)  # User, Owner, Admin
    role_id = db.Column(db.Integer, nullable=False)  # id of the user/owner/admin
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default="Pending")  # Pending, In Progress, Resolved
    
    # resolution details
    resolution = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
# contact for general inquiries
class GeneralInquiry(db.Model):
    __tablename__ = 'general_inquiry'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # response details
    response = db.Column(db.Text, nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    


# -----------------------
# Create Tables
# -----------------------

with app.app_context():
    db.create_all()
