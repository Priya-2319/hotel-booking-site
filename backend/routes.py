from hmac import new
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from app import app
from models import AdminCode, OwnerNotification, db, PropertyOwner, UserInfo, AdminInfo, PropertyInfo, UserBooking, BookingHistory, Review, RoomInfo
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import pycountry
from functools import wraps
from sqlalchemy.sql import func
import pytz
from sqlalchemy import and_, or_
from sqlalchemy import cast, Date
from datetime import date

ist = pytz.timezone('Asia/Kolkata')  # Indian Standard Time (IST)


import string
import secrets

import os
import random

#---------Decorators for login required----------------
def login_required_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'user' or 'user_id' not in session:
            flash('Please log in as a user to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_owner(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'owner' or 'owner_id' not in session:
            flash('Please log in as an owner to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin' or 'admin_id' not in session:
            flash('Please log in as an admin to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --------owner code generator-------------
def generate_owner_code(length=6):
    characters = string.ascii_uppercase + string.digits  # A-Z and 0-9
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_property_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.route('/')
def index():
    today_date = date.today()
    return render_template('base/home.html', date=today_date)

@app.route('/hotels')
def hotels():
    return render_template('base/hotels.html')

@app.route('/about')
def about():
    return render_template('base/about.html')

@app.route('/contact')
def contact():
    return render_template('base/contact.html')

@app.route('/terms & conditions')
def terms_conditions():
    now = datetime.now()
    return render_template('base/terms_and_conditions.html', now=now)

@app.route('/cancelation policy')
def cancelation_policy():
    now = datetime.now()
    return render_template('base/cancellation_policy.html', now=now)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        remember_me = request.form.get('remember') 
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return redirect(url_for('login'))
        
        if role == 'user':
            user = UserInfo.query.filter_by(email=email).first()
            if not user:
                flash('User not found or Invalid Email.', 'danger')
                return redirect(url_for('login'))
            if check_password_hash(user.password, password):
                # Set user session
                session['user_id'] = user.id
                session['user_name'] = user.name
                
                if remember_me:
                    session.permanent = True
                else:
                    session.permanent = False
                # Set role in session
                session['role'] = 'user'
                flash('Login successful!', 'success')
                return redirect(url_for('user_dashboard'))
            flash('Invalid password', 'danger')
            return redirect(url_for('login'))
        
        if role == 'owner':
            owner = PropertyOwner.query.filter_by(email=email).first()
            if not owner:
                flash('Owner not found or Invalid Email.', 'danger')
                return redirect(url_for('login'))
            if check_password_hash(owner.password, password):
                session['owner_id'] = owner.id
                session['owner_code'] = owner.owner_code
                session['owner_name'] = owner.name
                if remember_me:
                    session.permanent = True
                else:
                    session.permanent = False
                # Set role in session
                session['role'] = 'owner'
                flash('Login successful!', 'success')
                return redirect(url_for('owner_dashboard'))
            flash('Invalid password', 'danger')
            return redirect(url_for('login'))
        
        if role == 'admin':
            admin = AdminInfo.query.filter_by(email=email).first()
            if not admin:
                flash('Admin not found or Invalid Email.', 'danger')
                return redirect(url_for('login'))
            if check_password_hash(admin.password, password):
                session['admin_id'] = admin.id
                session['admin_code'] = admin.admin_code
                session['admin_name'] = admin.name
                if remember_me:
                    session.permanent = True
                else:
                    session.permanent = False
                session['role'] = 'admin'
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            flash('Invalid password', 'danger')
            return redirect(url_for('login'))
        
        flash('Invalid email or password.', 'danger')
        return redirect(url_for('login'))
    
    return render_template('base/login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        phone = request.form.get('phone', '').strip()
        dob = request.form.get('dob', '').strip()
        terms = request.form.get('terms')
        if not terms:
            flash('You must accept the terms and conditions.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        if not all ([role, name, email, password, confirm_password, phone]):
            flash ('All fields are required.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('register'))
        
        current_datetime = datetime.now(ist)
            
        if role == 'user':
            already_exist_user = UserInfo.query.filter_by(email=email).first()
            if already_exist_user:
                flash('A user with this email already exists.', 'danger')
                return redirect(url_for('register'))
            
            try:
                new_user = UserInfo(
                    name=name,
                    email=email,
                    password=hashed_password,
                    phone=phone,
                    dob=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
                    created_at=current_datetime,
                )
                db.session.add(new_user)
                db.session.commit()
                flash('User registered successfully!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error registering user: {str(e)}', 'danger')
                return redirect(url_for('register'))
        
        if role == 'owner':
            address = request.form.get('address', '').strip()
            id_type = request.form.get('id_type', '').strip()
            id_number = request.form.get('id_number', '').strip()
               
            already_exist_owner = PropertyOwner.query.filter_by(email=email).first()
            
            if already_exist_owner:
                flash('An owner with this email already exists.', 'danger')
                return redirect(url_for('register'))
            
            owner_code = generate_owner_code()
            if not owner_code:
                flash('Failed to generate owner code.', 'danger')
                return redirect(url_for('register'))
            
            try:
                new_owner = PropertyOwner(
                    owner_code=owner_code,
                    name=name,
                    email=email,
                    password=hashed_password,
                    phone=phone,
                    dob=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
                    address=address,
                    id_type=id_type,
                    id_number=id_number,
                    created_at=current_datetime,
                )
                db.session.add(new_owner)
                db.session.commit()
                flash('Owner registered successfully!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error registering owner: {str(e)}', 'danger')
                return redirect(url_for('register'))
            
        if role == 'admin':
            admin_code_input = request.form.get('admin_code', '').strip()

            if not admin_code_input:
                flash('Admin code is required for admin registration.', 'danger')
                return redirect(url_for('register'))

            # admin check
            existing_admin_code = AdminInfo.query.filter_by(admin_code=admin_code_input).first()
            if existing_admin_code:
                flash('An admin with this admin code already exists.', 'danger')
                return redirect(url_for('register'))
            
            if admin_code_input == 'SADMIN349':
                # create super admin
                new_admin = AdminInfo(
                    name=name,
                    email=email,
                    password=generate_password_hash(password),
                    phone=phone,
                    dob=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
                    admin_code=admin_code_input,
                    created_at=current_datetime,
                    status='Active'
                )
                db.session.add(new_admin)
                db.session.commit()
                flash('Super Admin registered successfully!', 'success')
                return redirect(url_for('login'))
            
            
            # Check if code exists in AdminCode table
            admin_code_entry = AdminCode.query.filter_by(code=admin_code_input).first()
            if not admin_code_entry:
                flash('Invalid admin code.', 'danger')
                return redirect(url_for('register'))

            # Check if code is already used
            if admin_code_entry.status == 'Used':
                flash('This admin code is already in use. Please contact support.', 'danger')
                return redirect(url_for('register'))

            # Check email uniqueness
            already_exist_admin = AdminInfo.query.filter_by(email=email).first()
            if already_exist_admin:
                flash('An admin with this email already exists.', 'danger')
                return redirect(url_for('register'))

            # Check phone uniqueness
            existing_phone = AdminInfo.query.filter_by(phone=phone).first()
            if existing_phone:
                flash('An admin with this phone number already exists.', 'danger')
                return redirect(url_for('register'))

            try:
                new_admin = AdminInfo(
                    name=name,
                    email=email,
                    password=generate_password_hash(password),
                    phone=phone,
                    dob=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
                    admin_code=admin_code_input,
                    created_at=datetime.utcnow(),
                    status='Active'
                )
                db.session.add(new_admin)
                db.session.commit()

                # Mark the admin code as used
                admin_code_entry.status = 'Used'
                admin_code_entry.admin_id = new_admin.id
                db.session.commit()

                flash('Admin registered successfully!', 'success')
                return redirect(url_for('login'))

            except Exception as e:
                db.session.rollback()
                flash(f'Error registering admin: {str(e)}', 'danger')
                return redirect(url_for('register'))

    return render_template('base/register.html')

# routes side not base routes-------------------------
from sqlalchemy import func, extract
from sqlalchemy import extract
from datetime import datetime, timedelta

@app.route('/owner_dashboard')
@login_required_owner
def owner_dashboard():
    owner_id = session.get("owner_id")
    current_user_name = session.get('owner_name')

    owner = PropertyOwner.query.get_or_404(owner_id)
    property_ids = [p.id for p in owner.properties]

    today = datetime.now().date()

    # -----------------------
    # Upcoming Bookings for Calendar
    # -----------------------
    upcoming_bookings = UserBooking.query.filter(
        UserBooking.property_id.in_(property_ids),
        UserBooking.end_date >= today
    ).order_by(UserBooking.start_date.asc()).all()

    # Convert to dictionary per day
    calendar_events = {}
    for booking in upcoming_bookings:
        start_date = booking.start_date.date()
        if start_date not in calendar_events:
            calendar_events[start_date] = []
        calendar_events[start_date].append({
            'time': booking.start_date.strftime("%I:%M %p"),
            'title': f"Check-in - {booking.property.property_name}",
            'guest': booking.user.name,
            'booking_code': booking.booking_code
        })

    # -----------------------
    # Other dashboard data (existing)
    # -----------------------
    total_properties = len(property_ids)

    today_date = date.today()
    today_bookings = UserBooking.query.filter(
        UserBooking.property_id.in_(property_ids),
        cast(UserBooking.start_date, Date) <= today_date,
        cast(UserBooking.end_date, Date) >= today_date
    ).count()

    current_month = datetime.now().month
    current_year = datetime.now().year

    completed_bookings = UserBooking.query.filter(
        UserBooking.property_id.in_(property_ids),
        UserBooking.status == 'Completed',
        extract('month', UserBooking.start_date) == current_month,
        extract('year', UserBooking.start_date) == current_year
    ).all()

    monthly_revenue = sum(
        (b.end_date.date() - b.start_date.date()).days * b.room.price_per_night
        for b in completed_bookings
    )
    monthly_revenue = round(monthly_revenue, 2)

    one_week_ago = datetime.today() - timedelta(days=7)
    new_reviews = Review.query.filter(
        Review.property_id.in_(property_ids),
        Review.review_date >= one_week_ago
    ).count()

    recent_reviews_details = Review.query.filter(
        Review.property_id.in_(property_ids)
    ).order_by(Review.review_date.desc()).limit(5).all()

    current_time = datetime.now()

    total_rating = db.session.query(func.sum(Review.rating)).filter(
        Review.property_id.in_(property_ids)
    ).scalar() or 0
    total_reviews_count = db.session.query(func.count(Review.id)).filter(
        Review.property_id.in_(property_ids)
    ).scalar() or 0
    average_rating = round(total_rating / total_reviews_count, 2) if total_reviews_count > 0 else 0

    recent_bookings = UserBooking.query.filter(
        UserBooking.property_id.in_(property_ids)
    ).order_by(UserBooking.booking_date.desc()).limit(5).all()

    property_revenues = []
    for p in owner.properties:
        p_bookings = [b for b in p.bookings if b.status == 'Completed']
        revenue = sum((b.end_date.date() - b.start_date.date()).days * b.room.price_per_night for b in p_bookings)
        property_revenues.append((p, revenue))
    top_by_revenue = sorted(property_revenues, key=lambda x: x[1], reverse=True)[:5]

    return render_template(
        'owner_side/dashboard.html',
        user_name=current_user_name,
        total_properties=total_properties,
        today_bookings=today_bookings,
        monthly_revenue=monthly_revenue,
        new_reviews=new_reviews,
        average_rating=average_rating,
        recent_bookings=recent_bookings,
        top_by_revenue=top_by_revenue,
        recent_reviews_details=recent_reviews_details,
        current_time=current_time,
        calendar_events=calendar_events
    )




# routes for owner side-------------------------
@app.route('/owner_dashboard/owner_properties')
@login_required_owner
def owner_properties():
    owner_id = session.get('owner_id')
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'newest')  # default sorting

    # --- Base Query ---
    query = PropertyInfo.query.filter_by(owner_id=owner_id)

    if search_query:
        query = query.filter(PropertyInfo.property_name.ilike(f'%{search_query}%'))

    # --- Fetch Properties ---
    properties = query.all()

    # --- Stats ---
    total_properties = len(properties)

    # Ratings & Revenue maps
    property_ratings = {}
    property_revenues = {}
    overall_rating_sum = 0
    monthly_revenue = 0

    # For occupancy calculation
    total_nights = 0
    booked_nights = 0

    today = datetime.now().date()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    for p in properties:
        # --- Avg Rating ---
        avg_rating = db.session.query(func.avg(Review.rating)).filter_by(property_id=p.id).scalar()
        avg_rating = round(avg_rating or 0, 1)
        property_ratings[p.id] = avg_rating
        overall_rating_sum += avg_rating

        # --- Monthly Revenue ---
        # revenue = (
        #     db.session.query(func.sum(Payment.amount))
        #     .join(UserBooking, UserBooking.id == Payment.booking_id)
        #     .filter(
        #         UserBooking.property_id == p.id,
        #         Payment.payment_date >= first_day,
        #         Payment.payment_date <= last_day
        #     )
        #     .scalar()
        # )
        # revenue = revenue or 0
        # property_revenues[p.id] = revenue
        # monthly_revenue += revenue

        # --- Occupancy ---
        bookings = UserBooking.query.filter_by(property_id=p.id).all()
        for b in bookings:
            total_nights += (b.end_date - b.start_date).days
            # Count only completed/active bookings
            if b.status in ("Confirmed", "Checked-in", "Completed"):
                booked_nights += (b.end_date - b.start_date).days

    # --- Overall Stats ---
    avg_overall_rating = round(overall_rating_sum / total_properties, 1) if total_properties > 0 else 0
    occupancy_rate = round((booked_nights / total_nights) * 100, 1) if total_nights > 0 else 0

    # --- Sorting ---
    if sort_by == "highest_revenue":
        properties.sort(key=lambda x: property_revenues.get(x.id, 0), reverse=True)
    elif sort_by == "highest_rating":
        properties.sort(key=lambda x: property_ratings.get(x.id, 0), reverse=True)
    elif sort_by == "most_bookings":
        properties.sort(key=lambda x: len(UserBooking.query.filter_by(property_id=x.id).all()), reverse=True)
    elif sort_by == "oldest":
        properties.sort(key=lambda x: x.created_at)
    else:  # newest
        properties.sort(key=lambda x: x.created_at, reverse=True)

    return render_template(
        'owner_side/crud_temp/owner_properties.html',
        properties=properties,
        search_query=search_query,
        total_properties=total_properties,
        property_ratings=property_ratings,
        property_revenues=property_revenues,
        avg_overall_rating=avg_overall_rating,
        monthly_revenue=2000,
        occupancy_rate=occupancy_rate,
        sort_by=sort_by
    )


@app.route('/owner_dashboard/add_property', methods=['GET', 'POST'])
@login_required_owner
def add_property():
    countries = sorted(
        [(country.alpha_2, country.name) for country in pycountry.countries],
        key=lambda x: x[1]
    )

    if request.method == 'POST':
        # Extract form data
        property_name = request.form.get('property_name')
        property_type = request.form.get('property_type')
        short_description = request.form.get('short_description')
        guest_capacity = request.form.get('guest_capacity')
        bedroom_count = request.form.get('bedroom_count')
        bathroom_count = request.form.get('bathroom_count')
        property_size = request.form.get('property_size')
        street_address = request.form.get('street_address')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        country = request.form.get('country')
        full_description = request.form.get('full_description')
        amenities_list = request.form.getlist('amenities[]')
        additional_amenities = request.form.get('additional_amenities')
        nearby = request.form.get('nearby')
        
        amenities = ','.join(amenities_list) if amenities_list else None

        # Handle photos
        photo_files = request.files.getlist('property_photos[]')
        photo_paths = []

        upload_folder = os.path.join(app.root_path, 'static/uploads/property_photos')
        os.makedirs(upload_folder, exist_ok=True)

        for file in photo_files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                relative_path = f'static/uploads/property_photos/{filename}'
                photo_paths.append(relative_path)

        photo_urls = ','.join(photo_paths)

        # Generate unique property code
        prop_code = generate_property_code()
        while PropertyInfo.query.filter_by(prop_code=prop_code).first():
            prop_code = generate_property_code()
            
        current_user = session.get('owner_id')
        if not current_user:
            flash('You must be logged in as an owner to add a property.', 'danger')
            return redirect(url_for('login'))

        # Create new property
        new_property = PropertyInfo(
            prop_code=prop_code,
            property_name=property_name,
            property_type=property_type,
            short_description=short_description,
            guest_capacity=int(guest_capacity),
            bedroom_count=int(bedroom_count),
            bathroom_count=int(bathroom_count),
            property_size=float(property_size),
            street_address=street_address,
            city=city,
            state=state,
            zip_code=int(zip_code),
            country=country,
            full_description=full_description,
            amenities=amenities,
            additional_amenities=additional_amenities,
            nearby=nearby,
            property_photos=photo_urls,
            owner_id=current_user # Ensure the user is logged in
        )

        db.session.add(new_property)
        db.session.commit()

        flash('Property added successfully!', 'success')
        return redirect(url_for('owner_properties'))  # Replace with your actual route

    return render_template(
        'owner_side/crud_temp/add_property.html',
        countries=countries
    )
    
@app.route('/property/<int:property_id>')
@login_required_owner
def view_property(property_id):
    property = PropertyInfo.query.get_or_404(property_id)
    return render_template('owner_side/crud_temp/view_property.html', property=property)
    
@app.route('/owner_dashboard/edit_property/<int:property_id>', methods=['GET', 'POST'])
@login_required_owner
def edit_property(property_id):
    property = PropertyInfo.query.get_or_404(property_id)
    countries = sorted([(c.alpha_2, c.name) for c in pycountry.countries], key=lambda x: x[1])

    if request.method == 'POST':
        # --- 1. Simple fields (unchanged) ----------------------------------
        property.property_name      = request.form.get('property_name')
        property.property_type      = request.form.get('property_type')
        property.short_description  = request.form.get('short_description')
        property.guest_capacity     = int(request.form.get('guest_capacity') or 0)
        property.bedroom_count      = int(request.form.get('bedroom_count') or 0)
        property.bathroom_count     = int(request.form.get('bathroom_count') or 0)
        property.property_size      = float(request.form.get('property_size') or 0)
        property.street_address     = request.form.get('street_address')
        property.city               = request.form.get('city')
        property.state              = request.form.get('state')
        property.zip_code           = request.form.get('zip_code')
        property.country            = request.form.get('country')
        property.full_description   = request.form.get('full_description')
        property.amenities          = ','.join(request.form.getlist('amenities[]'))
        property.additional_amenities = request.form.get('additional_amenities')
        property.nearby             = request.form.get('nearby')

        # -------------------------------------------------------------------
        # A) Collect current photo list
        existing = property.property_photos.split(',')

        # # B) Remove photos flagged by the form
        deleted  = request.form.get('deleted_photos', '').split(',')
        existing = [p for p in existing if p not in deleted]
        
        # OPTIONAL: physically delete files
        for rel_path in deleted:
            abs_path = os.path.join(app.root_path, rel_path.lstrip('/'))
            if os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                except OSError:
                    app.logger.warning(f"Could not delete {abs_path}")

        # C) Add any newly‑uploaded photos
        upload_folder = os.path.join(app.root_path, 'static/uploads/property_photos')
        os.makedirs(upload_folder, exist_ok=True)

        for file in request.files.getlist('property_photos[]'):
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                existing.append(f'static/uploads/property_photos/{filename}')

        # -------------------------------------------------------------------
        property.property_photos = ','.join(existing)
        db.session.commit()
        flash('Property updated successfully!', 'success')
        return redirect(url_for('owner_properties'))

    # GET: render form
    amenities_list = property.amenities.split(',') if property.amenities else []
    return render_template('owner_side/crud_temp/edit_property.html',
                           property=property,
                           countries=countries,
                           amenities_list=amenities_list)

    
@app.route('/owner_dashboard/property_analytics')
@login_required_owner
def property_analytics():
    return render_template('owner_side/crud_temp/property_analytics.html')

@app.route('/owner_dashboard/booking_reports')
@login_required_owner
def booking_reports():
    return render_template('owner_side/crud_temp/booking_reports.html')

@app.route('/owner_dashboard/owner_settings')
@login_required_owner
def owner_settings():
    return render_template('owner_side/crud_temp/owner_settings.html')

@app.route('/owner_dashboard/owner_calendar')
@login_required_owner
def owner_calendar():
    return render_template('owner_side/crud_temp/owner_calendar.html')

@app.route('/property/<int:property_id>/add-room', methods=['GET', 'POST'])
@login_required_owner
def add_room(property_id):
    property = PropertyInfo.query.get_or_404(property_id)
    if not property:
        flash('Property not found.', 'danger')
        return redirect(url_for('owner_properties'))
    
    if request.method == 'POST':
        try:
            # Get form data
            room_number = request.form.get('room_number')
            no_of_rooms = request.form.get('no_of_rooms', type=int, default=1)
            room_type = request.form.get('room_type')
            description = request.form.get('description')
            price_per_night = float(request.form.get('price_per_night'))
            capacity = int(request.form.get('guest_capacity'))
            roomSize = float(request.form.get('roomSize'))
            bed_type = request.form.get('bed_type')
            amenities_list = request.form.getlist('amenities[]')
            
            amenities = ','.join(amenities_list) if amenities_list else None
            
            # Handle photos
            photo_files = request.files.getlist('roomPhotos[]')
            photo_paths = []

            upload_folder = os.path.join(app.root_path, 'static/uploads/room_photos')
            os.makedirs(upload_folder, exist_ok=True)

            for file in photo_files:
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    relative_path = f'static/uploads/room_photos/{filename}'
                    photo_paths.append(relative_path)

            photo_urls = ','.join(photo_paths)
            
            # Create new room
            new_room = RoomInfo(
                room_number=room_number,
                no_of_rooms=no_of_rooms,
                room_type=room_type,
                description=description,
                price_per_night=price_per_night,
                capacity=capacity,
                room_size=roomSize,
                bed_type=bed_type,
                amenities=amenities,
                image_url=photo_urls,
                property_id=property.id  # Associate with the property
            )
            
            db.session.add(new_room)
            db.session.commit()
            flash('Room added successfully!', 'success')
            return redirect(url_for('view_property', property_id=property_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding room: {str(e)}', 'danger')
    
    return render_template('owner_side/crud_temp/add_room.html', property=property)

@app.route('/room/view/<int:room_id>')
@login_required_owner
def view_room(room_id):
    room = RoomInfo.query.get_or_404(room_id)
    # Convert amenities string to list if stored as JSON
    if room.amenities:
        amenities = room.amenities.split(',')
    else:
        amenities = []
        
    return render_template('owner_side/crud_temp/view_room.html', room=room, amenities=amenities)

@app.route('/property/<int:property_id>/edit-room/<int:room_id>', methods=['GET', 'POST'])
@login_required_owner
def edit_room(property_id, room_id):
    property = PropertyInfo.query.get_or_404(property_id)
    room = RoomInfo.query.get_or_404(room_id)

    if not property or not room or room.property_id != property.id:
        flash('Property or room not found.', 'danger')
        return redirect(url_for('owner_properties'))

    if request.method == 'POST':
        try:
            # ---------------------------------------------------------------
            # 0) Simple field updates          (unchanged)
            # ---------------------------------------------------------------
            room.room_number       = request.form.get('room_number')
            room.room_type         = request.form.get('room_type')
            room.description       = request.form.get('description')
            room.price_per_night   = float(request.form.get('price_per_night') or 0)
            room.capacity          = int(request.form.get('guest_capacity') or 0)
            room.room_size         = float(request.form.get('roomSize') or 0)
            room.bed_type          = request.form.get('bed_type')

            amenities_list = request.form.getlist('amenities[]')
            room.amenities = ','.join(amenities_list) if amenities_list else None

            # ---------------------------------------------------------------
            # A) Normalise current photo list
            # ---------------------------------------------------------------
            current_photos = [p.strip()                                           # trim spaces
                              for p in (room.image_url.split(',') if room.image_url else [])
                              if p.strip()]                                       # drop empties

            # ---------------------------------------------------------------
            # B) Remove photos flagged for deletion (and delete files)
            # ---------------------------------------------------------------
            deleted_photos = {p.lstrip('/').strip()                               # normalise
                              for p in request.form.get('deleted_photos', '').split(',')
                              if p.strip()}

            updated_photos = [p for p in current_photos if p.lstrip('/') not in deleted_photos]

            # optional –‑ remove the files from disk
            for rel in deleted_photos:
                abs_path = os.path.join(app.root_path, rel)
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                    except OSError:
                        app.logger.warning(f'Could not delete {abs_path}')

            # ---------------------------------------------------------------
            # C) Handle newly‑uploaded photos
            # ---------------------------------------------------------------
            upload_folder = os.path.join(app.root_path, 'static/uploads/room_photos')
            os.makedirs(upload_folder, exist_ok=True)

            for file in request.files.getlist('roomPhotos[]'):
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(upload_folder, filename))
                    updated_photos.append(f'static/uploads/room_photos/{filename}')

            # ---------------------------------------------------------------
            # Finalise and commit
            # ---------------------------------------------------------------
            room.image_url = ','.join(updated_photos) if updated_photos else None

            db.session.commit()
            flash('Room updated successfully!', 'success')
            return redirect(url_for('view_property', property_id=property_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating room: {e}', 'danger')

    return render_template('owner_side/crud_temp/edit_room.html',
                           property=property,
                           room=room)

@app.route('/property/<int:property_id>/delete-room/<int:room_id>', methods=['GET'])
@login_required_owner
def delete_room(property_id, room_id):
    # Verify the room exists and belongs to the property
    room = RoomInfo.query.filter_by(
        id=room_id,
        property_id=property_id
    ).first_or_404()

    try:
        # Store image paths before deletion
        image_paths = room.image_url.split(',') if room.image_url else []
        
        # Delete from database
        db.session.delete(room)
        db.session.commit()
        
        # Delete associated images
        for path in image_paths:
            path = path.strip()
            if path.startswith('static/'):  # Security check
                abs_path = os.path.join(app.root_path, path)
                try:
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                except Exception as e:
                    app.logger.error(f"Error deleting image {path}: {str(e)}")
        
        flash('Room deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting room: {str(e)}")
        flash('Failed to delete room', 'danger')
    
    return redirect(url_for('view_property', property_id=property_id))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        dob = request.form.get('dob', '').strip()
        new_password = request.form.get('new_password', '').strip()
        if not email:
            flash('Email is required.', 'danger')
            return redirect(url_for('forgot_password'))
        
        if not new_password:
            flash('New password is required.', 'danger')
            return redirect(url_for('forgot_password'))
        
        if not dob:
            flash('Date of birth is required for verification.', 'danger')
            return redirect(url_for('forgot_password'))
        
        user = UserInfo.query.filter_by(email=email).first()
        owner = PropertyOwner.query.filter_by(email=email).first()
        admin = AdminInfo.query.filter_by(email=email).first()
        
        if user:
            if dob and user.dob != datetime.strptime(dob, '%Y-%m-%d').date():
                flash('Date of birth does not match.', 'danger')
                return redirect(url_for('forgot_password'))
            
            new_user_password = generate_password_hash(new_password)
            user.password = new_user_password
            db.session.commit()
            flash('Password reset successfully.', 'success')
            return redirect(url_for('login'))
        elif owner:
            new_owner_password = generate_password_hash(new_password)
            owner.password = new_owner_password
            db.session.commit()
            flash('Password reset successfully.', 'success')
            return redirect(url_for('login'))
        elif admin:
            new_admin_password = generate_password_hash(new_password)
            admin.password = new_admin_password
            db.session.commit()
            flash('Password reset successfully.', 'success')
            return redirect(url_for('login'))
        else:
            flash('No user found with that email address.', 'danger')
            return redirect(url_for('forgot_password'))
    
    return render_template('base/forgot_password.html')


# owner can view bookings under their properties
@app.route('/owner_dashboard/owner_bookings')
@login_required_owner
def owner_bookings():
    owner_id = session.get('owner_id')
    if not owner_id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("owner_login"))

    # Get owner
    owner = PropertyOwner.query.get_or_404(owner_id)

    # All property IDs owned by this owner
    property_ids = [p.id for p in owner.properties]

    # Active bookings (check-out >= today)
    # Define Indian timezone
    ist = pytz.timezone("Asia/Kolkata")

    # Current date in IST
    today = datetime.now(ist).date()

    # Active bookings = not started OR ongoing today
    active_bookings = (
    UserBooking.query
    .filter(
        UserBooking.property_id.in_(property_ids),
        or_(
            func.date(UserBooking.start_date) > today,  # future
            and_(
                func.date(UserBooking.start_date) <= today,
                func.date(UserBooking.end_date) >= today   # ✅ includes same-day checkout
            )
        )
    )
    .order_by(UserBooking.start_date.asc())
    .all()
    )

    # Booking history = already finished
    booking_history = (
        BookingHistory.query
        .filter(
            BookingHistory.property_id.in_(property_ids),
            func.date(BookingHistory.end_date) < today
        )
        .order_by(BookingHistory.booking_date.desc())
        .all()
    )

    return render_template(
        "owner_side/crud_temp/owner_bookings.html",
        owner=owner,
        active_bookings=active_bookings,
        booking_history=booking_history
    )


# Owner can view upcoming confirmed bookings
@app.route('/owner_dashboard/upcoming_bookings')
@login_required_owner
def upcoming_bookings():
    owner_id = session.get('owner_id')
    if not owner_id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("owner_login"))

    owner = PropertyOwner.query.get_or_404(owner_id)
    property_ids = [p.id for p in owner.properties]

    # Upcoming confirmed bookings
    upcoming_bookings = (
        UserBooking.query
        .filter(
            UserBooking.property_id.in_(property_ids),
            UserBooking.status == "Confirmed",
            UserBooking.start_date >= datetime.now()
        )
        .order_by(UserBooking.start_date.asc())
        .all()
    )

    return render_template(
        "owner_side/crud_temp/upcoming_bookings.html",
        owner=owner,
        upcoming_bookings=upcoming_bookings
    )
    
# Owner can view reviews of their properties
@app.route('/owner_dashboard/owner_reviews')
@login_required_owner
def property_reviews():
    owner_id = session.get('owner_id')
    if not owner_id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("owner_login"))

    owner = PropertyOwner.query.get_or_404(owner_id)
    property_ids = [p.id for p in owner.properties]

    # Fetch all reviews for properties owned by this owner
    reviews = (
        Review.query
        .filter(Review.property_id.in_(property_ids))
        .order_by(Review.review_date.desc())
        .all()
    )

    return render_template(
        'owner_side/crud_temp/property_reviews.html',
        owner=owner,
        reviews=reviews
    )
    
# Owner can view the latest 5 reviews for their properties
@app.route('/owner_dashboard/latest_reviews')
@login_required_owner
def new_reviews():
    owner_id = session.get('owner_id')
    if not owner_id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("owner_login"))

    owner = PropertyOwner.query.get_or_404(owner_id)
    property_ids = [p.id for p in owner.properties]

    # Fetch latest 5 reviews
    latest_reviews = (
        Review.query
        .filter(Review.property_id.in_(property_ids))
        .order_by(Review.review_date.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'owner_side/crud_temp/new_reviews.html',
        owner=owner,
        latest_reviews=latest_reviews
    )


# Owner Profile Route
@app.route('/owner_dashboard/profile', methods=['GET', 'POST'])
@login_required_owner
def owner_profile():
    # fetch owner id from session
    owner_id = session.get('owner_id')
    owner = PropertyOwner.query.get_or_404(owner_id)

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        dob_str = request.form.get('dob')
        address = request.form.get('address')
        id_type = request.form.get('id_type')
        id_number = request.form.get('id_number')
        profile_pic = request.files.get('profile_pic')

        # convert dob string to date
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None

        owner.name = name
        owner.email = email
        owner.phone = phone
        owner.dob = dob
        owner.address = address
        owner.id_type = id_type
        owner.id_number = id_number

        # save profile picture if uploaded
        if profile_pic:
            folder_path = "static/profiles_pictures/owner_profile_pic"
            os.makedirs(folder_path, exist_ok=True)

            # delete old profile pic if exists
            if owner.profile_picture:
                old_pic_path = os.path.join(folder_path, owner.profile_picture)
                if os.path.exists(old_pic_path):
                    os.remove(old_pic_path)

            # save new picture
            pic_filename = f"owner_{owner.id}_{secure_filename(profile_pic.filename)}"
            profile_pic.save(os.path.join(folder_path, pic_filename))
            owner.profile_picture = pic_filename

        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('owner_profile'))

    return render_template('owner_side/crud_temp/owner_profile.html', owner=owner)

@app.route('/owner_dashboard/notifications')
@login_required_owner
def owner_notifications():
    owner_id = session.get("owner_id")
    if not owner_id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("owner_login"))

    # unread and all notifications
    unread_count = OwnerNotification.query.filter_by(owner_id=owner_id, is_read=False).count()
    notifications = (
        OwnerNotification.query
        .filter_by(owner_id=owner_id)
        .order_by(OwnerNotification.created_at.desc())
        .all()
    )

    return render_template(
        "owner_side/crud_temp/owner_notifications.html",
        notifications=notifications,
        unread_count=unread_count
    )
    
    
@app.route("/owner_dashboard/latest_updates")
@login_required_owner
def owner_latest_updates():
    owner_id = session.get("owner_id")
    if not owner_id:
        return jsonify({"error": "Unauthorized"}), 403

    owner = PropertyOwner.query.get_or_404(owner_id)
    property_ids = [p.id for p in owner.properties]

    # Latest booking
    latest_booking = (
        UserBooking.query
        .filter(UserBooking.property_id.in_(property_ids))
        .order_by(UserBooking.booking_date.desc())
        .first()
    )

    # Latest review
    latest_review = (
        Review.query
        .filter(Review.property_id.in_(property_ids))
        .order_by(Review.review_date.desc())
        .first()
    )
    
    # count of total reviews
    total_reviews = Review.query.filter(Review.property_id.in_(property_ids)).count()

    # Unread notifications count
    unread_count = OwnerNotification.query.filter_by(owner_id=owner_id, is_read=False).count()

    return jsonify({
        "unread_count": unread_count,
        "total_reviews": total_reviews,
        "latest_booking": {
            "booking_code": latest_booking.booking_code if latest_booking else None,
            "property": latest_booking.property.property_name if latest_booking else None,
        } if latest_booking else None,
        
        "latest_review": {
            "property": latest_review.property.property_name if latest_review else None,
            "rating": latest_review.rating if latest_review else None,
        } if latest_review else None
    })

@app.route('/owner/notifications/<filter_type>')
@login_required_owner
def owner_bookings_notifications(filter_type):
    owner_id = session.get("owner_id")
    if not owner_id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("owner_login"))

    # Base query: only "New Booking Received"
    query = OwnerNotification.query.filter_by(owner_id=owner_id).filter(
        OwnerNotification.title == "New Booking Received"
    )

    # Apply read/unread filters
    if filter_type == "unread":
        query = query.filter_by(is_read=False)
    elif filter_type == "read":
        query = query.filter_by(is_read=True)

    # Default "all booking notifications" → no is_read filter
    notifications = query.order_by(OwnerNotification.created_at.desc()).all()

    return render_template(
        "owner_side/crud_temp/owner_bookings_notifications.html",
        notifications=notifications,
        filter_type=filter_type
    )
    
@app.route('/owner/notifications/mark_read/<int:notif_id>', methods=['POST'])
@login_required_owner
def mark_owner_notification_read(notif_id):
    owner_id = session.get("owner_id")
    if not owner_id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("owner_login"))

    notif = OwnerNotification.query.filter_by(id=notif_id, owner_id=owner_id).first()
    if not notif:
        flash("Notification not found.", "danger")
        return redirect(url_for("owner_bookings_notifications", filter_type="all"))

    notif.is_read = True
    db.session.commit()
    flash("Notification marked as read.", "success")
    return redirect(url_for("owner_bookings_notifications", filter_type="all"))


@app.route('/owner/all_notifications/<filter_type>', methods=['GET'])
@login_required_owner
def owner_all_notifications(filter_type):
    owner_id = session.get('owner_id')
    if not owner_id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for("owner_login"))

    # Base query
    query = OwnerNotification.query.filter_by(owner_id=owner_id)

    # Filter notifications
    if filter_type == "unread":
        query = query.filter_by(is_read=False)
    elif filter_type == "read":
        query = query.filter_by(is_read=True)
    # else "all" shows everything

    # Sort latest first
    notifications = query.order_by(OwnerNotification.created_at.desc()).all()

    return render_template(
        "owner_side/crud_temp/owner_all_notifications.html",
        notifications=notifications,
        filter_type=filter_type
    )
    
@app.route('/owner/notifications_all/mark_read/<int:notification_id>', methods=['POST'])
@login_required_owner
def mark_notification_read(notification_id):
    owner_id = session.get('owner_id')
    notification = OwnerNotification.query.filter_by(id=notification_id, owner_id=owner_id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return {"status": "success"}