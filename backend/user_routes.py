from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from app import app
from models import OwnerNotification, db, PropertyOwner, UserInfo, AdminInfo, PropertyInfo, UserBooking, BookingHistory, Review, RoomInfo, UserNotification, UserNotificationRead
from backend.routes import login_required_user
from sqlalchemy import or_, and_, func
import os
import random, string
from datetime import datetime, time, date, timedelta
import pytz
from werkzeug.security import generate_password_hash, check_password_hash

ist = pytz.timezone('Asia/Kolkata')
# booking_date = datetime.now(ist)



def generate_unique_booking_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not UserBooking.query.filter_by(booking_code=code).first():
            return code


@app.route('/user_dashboard')
@login_required_user
def user_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view your dashboard.", "warning")
        return redirect(url_for('login'))

    today = date.today()

    # ----------------------------
    # Recent Bookings
    # ----------------------------
    bookings = (UserBooking.query
                .filter(UserBooking.user_id == user_id)
                .order_by(UserBooking.start_date.desc())
                .limit(6)
                .all())

    recent_bookings = []
    for b in bookings:
        start_d = b.start_date.date()
        end_d = b.end_date.date()

        if start_d > today:
            status = "Upcoming"
        elif end_d <= today:
            status = "Completed"
        else:
            status = "Ongoing"

        recent_bookings.append({
            "property_name": b.property.property_name,
            "image": b.property.property_photos.split(',')[0] if b.property.property_photos else '',
            "start_date": b.start_date.strftime('%b %d'),
            "end_date": b.end_date.strftime('%d, %Y'),
            "price": b.room.price_per_night,
            "status": status
        })

    # ----------------------------
    # Top Rated Hotels (for sidebar or luxury section)
    # ----------------------------
    top_rated = (
    db.session.query(PropertyInfo)
    .join(Review, Review.property_id == PropertyInfo.id)
    .group_by(PropertyInfo.id)
    .order_by(func.avg(Review.rating).desc())
    .limit(3)
    .all()
)

    return render_template(
        'user_side/dashboard.html',
        recent_bookings=recent_bookings,
        top_rated=top_rated,
        date=date
    )

@app.context_processor
def inject_user_name():
    return dict(user_name=session.get('user_name'))

# Inject Owner Info
@app.context_processor
def inject_owner_info():
    owner_id = session.get('owner_id')
    if owner_id:
        owner = PropertyOwner.query.get(owner_id)
        if owner:
            return dict(
                owner_name=owner.name,
                owner_code=owner.owner_code,
                owner_email=owner.email,
                owner_profile_pic=owner.profile_picture
            )
    return dict(
        owner_name=None,
        owner_code=None,
        owner_email=None,
        owner_profile_pic=None
    )

@app.context_processor
def inject_admin_name():
    admin_id = session.get('admin_id')
    if admin_id:
        admin = AdminInfo.query.get(admin_id)
        if admin:
            admin_name = admin.name
            admin_code = admin.admin_code
            admin_email = admin.email
            admin_profile_pic = admin.profile_picture
            return dict(admin_name=admin_name, admin_code=admin_code, admin_email=admin_email, admin_profile_pic=admin_profile_pic)
    return dict(admin_name=None, admin_code=None, admin_email=None, admin_profile_pic=None)

@app.route('/search', methods=['POST', 'GET'])
def property_search():
    if request.method == 'POST':
        # Read form values (from dashboard form)
        query = (request.form.get('q') or '').strip()
        check_in = (request.form.get('check_in') or '').strip()
        check_out = (request.form.get('check_out') or '').strip()
        guests = request.form.get('guests', type=int)
    else:
        # Read values from query string (GET - Trending Destinations)
        query = (request.args.get('destination') or '').strip()
        check_in = (request.args.get('check_in') or '').strip()
        check_out = (request.args.get('check_out') or '').strip()
        guests = request.args.get('guests', default=1, type=int)  # Default 1 guest

    # ---------- Required fields ----------
    if not query or not check_in or not check_out or not guests:
        flash('All fields are required.', 'danger')
        return redirect(url_for('user_dashboard'))

    # ---------- Guests validation ----------
    if guests <= 0:
        flash('Guests must be at least 1.', 'danger')
        return redirect(url_for('user_dashboard'))

    # ---------- Date validation ----------
    try:
        ci = datetime.strptime(check_in, '%Y-%m-%d').date()
        co = datetime.strptime(check_out, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
        return redirect(url_for('user_dashboard'))

    today = datetime.now(ist).date()
    if co <= ci:
        flash('Check-out date must be after check-in date.', 'danger')
        return redirect(url_for('user_dashboard'))
    if ci < today:
        flash('Check-in date cannot be in the past.', 'danger')
        return redirect(url_for('user_dashboard'))

    # ---------- Perform search ----------
    properties = PropertyInfo.query.filter(
        or_(
            PropertyInfo.city.ilike(f'%{query}%'),
            PropertyInfo.country.ilike(f'%{query}%'),
            PropertyInfo.property_name.ilike(f'%{query}%'),
            PropertyInfo.property_type.ilike(f'%{query}%'),
            PropertyInfo.street_address.ilike(f'%{query}%'),
            PropertyInfo.state.ilike(f'%{query}%'),
        ),
        PropertyInfo.guest_capacity >= guests
    ).all()

    today_date = datetime.now(ist)
    return render_template(
        'user_side/crud_temp/search_results.html',
        properties=properties,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        query=query,
        date=today_date
    )

@app.route('/user/property/<int:property_id>')
def view_property_and_book(property_id):
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    guests = request.args.get('guests', default=1, type=int)

    check_in_date = None
    check_out_date = None

    if check_in and check_out:
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

            if check_out_date <= check_in_date:
                flash('Check-out date must be after check-in date.', 'danger')
                return redirect(url_for('user_dashboard'))

            if check_in_date < datetime.now().date():
                flash('Check-in date cannot be in the past.', 'danger')
                return redirect(url_for('user_dashboard'))

        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
            return redirect(url_for('user_dashboard'))

    property = PropertyInfo.query.get_or_404(property_id)

    rooms = RoomInfo.query.filter_by(property_id=property_id, is_available=True).all()
    available_rooms = []

    for room in rooms:
        if not check_in_date or not check_out_date:
            available_rooms.append(room)
        else:
            overlapping = UserBooking.query.filter(
                UserBooking.room_id == room.id,
                UserBooking.status.in_(["Confirmed", "Checked-in"]),
                UserBooking.start_date < check_out_date,
                UserBooking.end_date > check_in_date
            ).count()

            # If you track room inventory count, adjust the condition accordingly
            if getattr(room, 'no_of_rooms', 1) > overlapping and room.capacity >= guests:
                available_rooms.append(room)

    return render_template(
        'user_side/crud_temp/view_property.html',
        property=property,
        rooms=available_rooms,
        check_in=check_in,
        check_out=check_out,
        guests=guests
    )

@app.route('/property/<int:property_id>/book', methods=['GET', 'POST'])
@login_required_user
def book_property(property_id):
    property = PropertyInfo.query.get_or_404(property_id)

    if request.method == 'POST':
        room_id = request.form.get('room_id', type=int)
        user_id = session.get('user_id')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        guests = request.form.get('guests', type=int)

        if not all([room_id, user_id, check_in, check_out]):
            flash("All booking fields are required.", "danger")
            return redirect(request.url)

        try:
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
            
            check_in_datetime = datetime.combine(check_in_date.date(), time(hour=12, minute=0))
            check_out_datetime = datetime.combine(check_out_date.date(), time(hour=11, minute=0))
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(request.url)
        
        booking = UserBooking(
            booking_code=generate_unique_booking_code(),
            booking_date=datetime.now(pytz.timezone("Asia/Kolkata")),
            user_id=user_id,
            property_id=property_id,
            room_id=room_id,
            start_date=check_in_datetime,
            end_date=check_out_datetime,
            status='Confirmed'
        )

        db.session.add(booking)
        
        # 🔔 Create notification for the property owner
        owner_notification = OwnerNotification(
            owner_id=property.owner_id,
            title="New Booking Received",
            message=f"A new booking has been made for {property.property_name} - {booking.booking_code}.",
            type="success",
            is_read=False,
            created_at=datetime.now(pytz.timezone("Asia/Kolkata"))
        )
        db.session.add(owner_notification)

        # 🔔 Create notification for the user
        user_notification = UserNotification(
            user_id=user_id,
            title="Booking Confirmed",
            message=f"Your booking {booking.booking_code} at {property.property_name} has been confirmed.",
            type="success",
            is_read=False,
            created_at=datetime.now(pytz.timezone("Asia/Kolkata"))
        )
        db.session.add(user_notification)
        
        db.session.commit()

        flash("Booking confirmed!", "success")
        return redirect(url_for('user_dashboard'))

    # GET method
    room_id = request.args.get('room_id', type=int)
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    guests = request.args.get('guests', type=int)

    room = RoomInfo.query.get(room_id) if room_id else None

    return render_template(
        'user_side/crud_temp/book_room.html',
        property=property,
        room=room,
        check_in=check_in,
        check_out=check_out,
        guests=guests
    )


@app.route('/my_bookings')
@login_required_user
def my_bookings():
    # Get current user id
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view your bookings.", "warning")
        return redirect(url_for('login'))

    # Get current date (IST if you're using that timezone)
    today = datetime.now().date()

    # Auto-update: mark past confirmed bookings as 'Completed'
    past_confirmed = UserBooking.query.filter(
        UserBooking.user_id == user_id,
        UserBooking.status == 'Confirmed',
        UserBooking.end_date < datetime.now()
    ).all()

    for booking in past_confirmed:
        booking.status = 'Completed'
        
        # add in bookinghistory
        archived = BookingHistory(
            booking_code=booking.booking_code,
            booking_date=booking.booking_date,
            start_date=booking.start_date,
            end_date=booking.end_date,
            status='Completed',
            user_id=booking.user_id,
            property_id=booking.property_id,
            room_id=booking.room_id
        )
        
        db.session.add(archived)

    if past_confirmed:
        db.session.commit()

    # Fetch all active bookings after updates
    active = (UserBooking.query
              .filter(UserBooking.user_id == user_id)
              .order_by(UserBooking.start_date.desc())
              .all())

    # Fetch archived cancelled bookings
    archived = (BookingHistory.query
                .filter_by(user_id=user_id, status='Cancelled')
                .order_by(BookingHistory.start_date.desc())
                .all())

    # Group active by date
    upcoming = []
    ongoing = []
    past    = []

    for b in active:
        start_d = b.start_date.date()
        end_d = b.end_date.date()

        if start_d > today and b.status == 'Confirmed':
            upcoming.append(b)
        elif end_d <= today:
            past.append(b)
        else:
            ongoing.append(b)

    return render_template(
        'user_side/crud_temp/my_bookings.html',
        upcoming=upcoming,
        ongoing=ongoing,
        past=past,
        archived=archived
    )
    
@app.route('/view_booking/<int:booking_id>')
def view_booking_page(booking_id):
    booking = UserBooking.query.get_or_404(booking_id)
    user_id = session.get('user_id')
    if booking.user_id != user_id:
        flash("You are not allowed to view this booking.", "danger")
        return redirect(url_for('my_bookings'))
    
    return render_template(
        'user_side/crud_temp/view_booking.html', booking=booking
    )

   
@app.post('/booking/<int:booking_id>/cancel')
@login_required_user
def cancel_booking(booking_id):
    booking = UserBooking.query.get_or_404(booking_id)
    user_id = session.get('user_id')

    if booking.user_id != user_id:
        flash("You are not allowed to cancel this booking.", "danger")
        return redirect(url_for('my_bookings'))

    today_ist = datetime.now(pytz.timezone("Asia/Kolkata")).date()
    if booking.start_date.date() <= today_ist:
        flash("This booking has already started or finished and cannot be cancelled.", "warning")
        return redirect(url_for('my_bookings'))

    try:
        # make cancelled
        booking.status = 'Cancelled'
        
        # Move to BookingHistory with status 'Cancelled'
        archived = BookingHistory(
            booking_code=booking.booking_code,
            booking_date=booking.booking_date,
            start_date=booking.start_date,
            end_date=booking.end_date,
            status='Cancelled',
            user_id=booking.user_id,
            property_id=booking.property_id,
            room_id=booking.room_id
        )

        db.session.add(archived)
        db.session.commit()

        flash("Your booking has been cancelled and archived.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Could not cancel booking: {e}", "danger")

    return redirect(url_for('my_bookings'))

# route for top destinations
@app.route('/top_destinations')
def top_destinations():
    today = datetime.now(ist).date()
    tomorrow = today + timedelta(days=1)

    cities = [
        "Banglore", "Mumbai", "Kashmir", "Chennai", "Kolkata", 
        "Ayodhaya", "Varanasi", "Agra", "Jaypur", "Delhi", "Goa", "Sikkim"
    ]

    return render_template(
        'user_side/crud_temp/top_destinations.html',
        cities=cities,
        today=today.strftime('%Y-%m-%d'),
        tomorrow=tomorrow.strftime('%Y-%m-%d')
    )

# Route for viewing and updating user profile
@app.route('/user_profile', methods=['GET', 'POST'])
@login_required_user
def user_profile():
    # Fetch user id from session
    user_id = session.get('user_id')
    user = UserInfo.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name').strip()
        email = request.form.get('email').strip()
        phone = request.form.get('phone').strip()
        dob_str = request.form.get('dob').strip()
        address = request.form.get('address').strip()
        id_type = request.form.get('id_type').strip()
        id_number = request.form.get('id_number').strip()
        profile_pic = request.files.get('profile_picture')

        # Check for duplicate phone number
        exists_phone = UserInfo.query.filter(UserInfo.phone == phone, UserInfo.id != user_id).first()
        if exists_phone:
            flash("Phone number already exists.", "danger")
            return redirect(url_for('user_profile'))

        # Convert DOB string to date
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None

        # Update user fields
        user.name = name
        user.email = email
        user.phone = phone
        user.dob = dob
        user.address = address
        user.id_type = id_type
        user.id_number = id_number
        user.updated_at = datetime.now()

        # Handle profile picture upload
        if profile_pic:
            # Define upload folder
            upload_folder = os.path.join('static', 'profiles_pictures', 'user_profile_pic')
            os.makedirs(upload_folder, exist_ok=True)

            # Delete old profile picture if exists
            if user.profile_picture:
                old_path = os.path.join(upload_folder, user.profile_picture)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Save new profile picture
            pic_filename = f"user_{user.id}_{profile_pic.filename}"
            profile_pic.save(os.path.join(upload_folder, pic_filename))
            user.profile_picture = pic_filename

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {e}', 'danger')

        return redirect(url_for('user_profile'))

    return render_template('user_side/crud_temp/user_profile.html', user=user)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required_user
def change_password():
    user_id = session.get('user_id')
    user = UserInfo.query.get_or_404(user_id)

    if request.method == 'POST':
        current_password = request.form.get('current_password').strip()
        new_password = request.form.get('new_password').strip()

        if not current_password or not new_password:
            flash("Both fields are required.", "danger")
            return redirect(url_for('change_password'))

        if not check_password_hash(user.password, current_password): 
            flash("Current password is incorrect.", "danger")
            return redirect(url_for('change_password'))

        user.password = generate_password_hash(new_password)
        try:
            db.session.commit()
            flash("Password changed successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

        return redirect(url_for('user_profile'))

    return render_template('user_side/crud_temp/user_profile.html', user=user)

# ----------------------------
# Reviews Page
# ----------------------------
@app.route('/reviews')
def reviews():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in first.", "danger")
        return redirect(url_for("user_login"))

    # Show bookings that already ended (eligible for review)
    completed_bookings = UserBooking.query.filter(
        UserBooking.user_id == user_id,
        UserBooking.end_date < datetime.now()
    ).all()

    # Get user’s existing reviews
    user_reviews = Review.query.filter_by(user_id=user_id).order_by(Review.review_date.desc()).all()

    return render_template(
        "user_side/crud_temp/user_reviews.html",
        completed_bookings=completed_bookings,
        user_reviews=user_reviews
    )
    
@app.route('/submit_review', methods=['POST'])
def submit_review():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in first.", "danger")
        return redirect(url_for("user_login"))

    booking_id = request.form.get("booking_id")
    rating = request.form.get("rating")
    comment = request.form.get("comment")

    if not booking_id or not rating:
        flash("Booking and rating are required.", "danger")
        return redirect(url_for("reviews"))

    booking = UserBooking.query.get(booking_id)
    if not booking or booking.user_id != user_id:
        flash("Invalid booking selected.", "danger")
        return redirect(url_for("reviews"))

    # Check if already reviewed
    if booking.review:
        flash("You have already reviewed this booking.", "warning")
        return redirect(url_for("reviews"))

    review = Review(
        booking_id=booking.id,
        user_id=user_id,
        property_id=booking.property_id,
        rating=int(rating),
        comment=comment
    )

    db.session.add(review)
    db.session.commit()

    flash("Thank you! Your review has been submitted.", "success")
    return redirect(url_for("reviews"))

# fetch user notifications
@app.context_processor
def inject_user_notifications():
    user_id = session.get('user_id')
    if user_id:
        notifications = (UserNotification.query
                         .filter(
                             (UserNotification.user_id == user_id) | 
                             (UserNotification.type == "All")
                         )
                         .order_by(UserNotification.created_at.desc())
                         .limit(5)
                         .all())

        unread_count = (UserNotification.query
                        .filter(
                            ((UserNotification.user_id == user_id) | 
                             (UserNotification.type == "All")) &
                            (UserNotification.is_read == False)
                        )
                        .count())

        return dict(user_notifications=notifications, unread_count=unread_count)
    
    return dict(user_notifications=[], unread_count=0)

# user all notifications
@app.route('/user/notifications')
@login_required_user
def view_user_notifications():
    user_id = session.get('user_id')

    # All notifications for this user + global ones
    notifications = (UserNotification.query
                     .filter((UserNotification.user_id == user_id) | (UserNotification.type == "All"))
                     .order_by(UserNotification.created_at.desc())
                     .all())

    # Build a dictionary of read global notifications
    read_global_ids = {r.notification_id for r in UserNotificationRead.query.filter_by(user_id=user_id).all()}

    return render_template("user_side/crud_temp/notifications.html", notifications=notifications, read_global_ids=read_global_ids)



@app.route('/mark_all_read')
def mark_all_read():
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to perform this action.", "warning")
        return redirect(url_for('login'))

    # Update all unread notifications
    UserNotification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()

    # flash("All notifications marked as read.", "success")
    return redirect(request.referrer or url_for('dashboard'))

# mark single notification as read
@app.route('/notifications/mark/<int:notification_id>')
@login_required_user
def mark_single_read(notification_id):
    user_id = session.get('user_id')
    notification = UserNotification.query.get_or_404(notification_id)

    if notification.type == "All":
        # Record that THIS user has read this global notification
        exists = UserNotificationRead.query.filter_by(user_id=user_id, notification_id=notification_id).first()
        if not exists:
            record = UserNotificationRead(user_id=user_id, notification_id=notification_id)
            db.session.add(record)
    else:
        # Normal user-specific notification
        if notification.user_id == user_id:
            notification.is_read = True

    db.session.commit()
    return redirect(url_for('view_user_notifications'))


