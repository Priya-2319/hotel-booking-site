import random
import string
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
import pytz
from app import app
from backend.routes import login_required_admin
from models import *
from datetime import datetime, time, timedelta
import os
from sqlalchemy import func, desc

@app.route('/api/dashboard-stats')
def notification_stats():
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)

    # Users in last 7 days
    users_count = UserInfo.query.filter(UserInfo.created_at >= seven_days_ago).count()

    # Owners in last 7 days
    owners_count = PropertyOwner.query.filter(PropertyOwner.created_at >= seven_days_ago).count()

    # Admins in last 7 days
    admins_count = AdminInfo.query.filter(AdminInfo.created_at >= seven_days_ago).count()

    # Pending properties
    pending_properties = PropertyInfo.query.filter_by(status="Pending").count()

    return jsonify({
        "users_last_7_days": users_count,
        "owners_last_7_days": owners_count,
        "admins_last_7_days": admins_count,
        "pending_properties": pending_properties
    })

# admin dashboard route

@app.route('/admin_dashboard')
@login_required_admin
def admin_dashboard():
    today_date = datetime.now().date()

    # total users
    total_users = UserInfo.query.count()

    # total property owners
    total_owners = PropertyOwner.query.count()

    # total properties
    total_properties = PropertyInfo.query.count()

    # revenue from completed bookings (BookingHistory)
    completed_bookings = (
        db.session.query(
            BookingHistory.start_date,
            BookingHistory.end_date,
            RoomInfo.price_per_night
        )
        .join(RoomInfo, BookingHistory.room_id == RoomInfo.id)
        .filter(BookingHistory.status == "Completed")
        .all()
    )

    revenue = 0
    for booking in completed_bookings:
        days = (booking.end_date - booking.start_date).days
        if days <= 0:
            days = 1
        revenue += days * booking.price_per_night

    # -------------------------
    # Recent Activity Section
    # -------------------------
    recent_users = UserInfo.query.order_by(desc(UserInfo.created_at)).limit(5).all()
    recent_properties = PropertyInfo.query.order_by(desc(PropertyInfo.created_at)).limit(5).all()
    recent_owners = PropertyOwner.query.order_by(desc(PropertyOwner.created_at)).limit(5).all()

    return render_template(
        'admin_side/dashboard.html',
        today_date=today_date,
        total_users=total_users,
        total_owners=total_owners,
        total_properties=total_properties,
        revenue=revenue,
        recent_users=recent_users,
        recent_properties=recent_properties,
        recent_owners=recent_owners
    )



# view users route
@app.route('/view_users')
@login_required_admin
def admin_view_users():
    users = UserInfo.query.all()
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/view_users.html', users=users, today_date=today_date)

# view user by id route
@app.route('/view_user/<int:user_id>')
@login_required_admin
def admin_view_user_details(user_id):
    user = UserInfo.query.get_or_404(user_id)
    return render_template('admin_side/crud_temp/view_user_details.html', user=user)

# deactivate user route
@app.route('/deactivate_user/<int:user_id>')
@login_required_admin
def admin_suspended_user(user_id):
    user = UserInfo.query.get_or_404(user_id)
    user.status = 'Suspended'
    db.session.commit()
    flash('User has been suspended successfully!', 'warning')
    return redirect(url_for('admin_view_users'))

# activate user route
@app.route('/activate_user/<int:user_id>')
@login_required_admin
def admin_activate_user(user_id):
    user = UserInfo.query.get_or_404(user_id)
    user.status = 'Active'
    db.session.commit()
    flash('User has been activated successfully!', 'success')
    return redirect(url_for('admin_view_users'))

# view owners route
@app.route('/view_owners')
@login_required_admin
def admin_view_owners():
    owners = PropertyOwner.query.all()
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/view_owners.html', owners=owners, today_date=today_date)

# upcoming booking route
@app.route('/active_bookings')
@login_required_admin
def admin_Upcoming_bookings():
    now = datetime.now()
    bookings = UserBooking.query.filter(
        UserBooking.start_date > now,
        UserBooking.status == 'Confirmed'
    ).all()
    
    return render_template(
        'admin_side/crud_temp/upcoming_bookings.html',
        bookings=bookings,
        today_date=now.date()
    )

# completed booking route
@app.route('/completed_bookings')
@login_required_admin
def admin_completed_bookings():
    bookings = BookingHistory.query.filter_by(status='Completed').all()
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/completed_bookings.html', bookings=bookings, today_date=today_date)

# cancelled booking route
@app.route('/cancelled_or_comp_bookings')
@login_required_admin
def admin_cancelled_or_comp_bookings():
    bookings = BookingHistory.query.all()
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/cancelled_bookings.html', bookings=bookings, today_date=today_date)

@app.route('/ongoing_bookings')
@login_required_admin
def admin_ongoing_bookings():
    today = datetime.now().date()
    start_of_day = datetime.combine(today, time.min)  # 00:00:00
    end_of_day = datetime.combine(today, time.max)    # 23:59:59

    bookings = UserBooking.query.filter(
        UserBooking.start_date <= end_of_day,
        UserBooking.end_date >= start_of_day,
        UserBooking.status == 'Confirmed'
    ).all()

    return render_template(
        'admin_side/crud_temp/ongoing_bookings.html',
        bookings=bookings,
        today_date=today
    )
# all bookings route
@app.route('/all_bookings')
@login_required_admin
def admin_all_bookings():
    bookings = UserBooking.query.all()
    today_date = datetime.now().date()
    # upcoming_bookings = []
    # completed_bookings = []
    # cancelled_bookings = []
    # ongoing_bookings = []
    bookings_with_status = []
    for booking in bookings:
        if booking.status == 'Confirmed':
            if booking.start_date.date() > today_date:
                # change booking status to Upcoming
                booking.status = 'Upcoming'
                bookings_with_status.append(booking)
            elif booking.start_date.date() <= today_date <= booking.end_date.date():
                # change booking status to Ongoing
                booking.status = 'Ongoing'
                bookings_with_status.append(booking)
        elif booking.status == 'Completed':
            booking.status = 'Completed'
            bookings_with_status.append(booking)
        elif booking.status == 'Cancelled':
            booking.status = 'Cancelled'
            bookings_with_status.append(booking)
    
    return render_template('admin_side/crud_temp/all_bookings.html', bookings=bookings_with_status, today_date=today_date)

# route for fetch all owners
@app.route('/all_owners')
@login_required_admin
def admin_all_owners():
    owners = PropertyOwner.query.all()
    today_date = datetime.now().date()
    # total properties
    total_properties = PropertyInfo.query.count()
    return render_template('admin_side/crud_temp/view_all_owners.html', owners=owners, today_date=today_date, total_properties=total_properties)

# view owner by id route
@app.route('/view_owner/<int:owner_id>')
@login_required_admin
def admin_view_owner_details(owner_id):
    owner = PropertyOwner.query.get_or_404(owner_id)
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/owner_details.html', owner=owner, today_date=today_date)

@app.route('/edit_owner/<int:owner_id>', methods=['GET', 'POST'])
@login_required_admin
def admin_edit_owner(owner_id):
    owner = PropertyOwner.query.get_or_404(owner_id)

    if request.method == 'POST':
        if request.form.get('deactivate'):
            owner.status = 'Deactivated'
            db.session.commit()
            flash('Owner has been deactivated successfully!', 'warning')
            return redirect(url_for('admin_edit_owner', owner_id=owner.id))

        if request.form.get('activate'):
            owner.status = 'Active'
            db.session.commit()
            flash('Owner has been activated successfully!', 'success')
            return redirect(url_for('admin_edit_owner', owner_id=owner.id))

    return render_template(
        'admin_side/crud_temp/admin_edit_owner.html',
        owner=owner
    )


# delete owner by id route
@app.route('/delete_owner/<int:owner_id>')
# @login_required_admin
def admin_delete_owner(owner_id):
    owner = PropertyOwner.query.get_or_404(owner_id)
    # First, delete all properties associated with the owner
    for property in owner.properties:
        db.session.delete(property)
    # Then, delete the owner
    db.session.delete(owner)
    db.session.commit()
    return redirect(url_for('admin_all_owners'))

# global admin details route
@app.route('/admin_details', methods=['GET', 'POST'])
@login_required_admin
def admin_details():
    admin = AdminInfo.query.first()  # Assuming there's only one admin
    today_date = datetime.now().date()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        dob_str = request.form.get('dob')
        address = request.form.get('address')
        
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
        
        admin.name = name
        admin.email = email
        admin.phone = phone
        admin.dob = dob
        admin.address = address
        
        db.session.commit()
        
        flash('Admin details updated successfully!', 'success')
        return redirect('/admin_details')
    
    return render_template('admin_side/crud_temp/admin_details.html', admin=admin, today_date=today_date)

# route for admin profile
@app.route('/admin_profile', methods=['GET', 'POST'])
@login_required_admin
def admin_profile():
    # fetch admin id from session
    admin_id = session.get('admin_id')
    admin = AdminInfo.query.get_or_404(admin_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        dob_str = request.form.get('dob')
        address = request.form.get('address')
        id_type = request.form.get('id_type')
        id_number = request.form.get('id_number')
        profile_pic = request.files.get('profile_pic')

        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None

        # Update fields
        admin.name = name
        admin.email = email
        admin.phone = phone
        admin.dob = dob
        admin.address = address
        admin.id_type = id_type
        admin.id_number = id_number

        if profile_pic:
            # Define save path
            upload_folder = os.path.join('static', 'profiles_pictures', 'admin_profile_pic')

            # Ensure directory exists
            os.makedirs(upload_folder, exist_ok=True)

            # Delete old profile picture if exists
            if admin.profile_picture:
                old_path = os.path.join(upload_folder, admin.profile_picture)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # Save new profile picture
            pic_filename = f"admin_{admin.id}_{profile_pic.filename}"
            profile_pic.save(os.path.join(upload_folder, pic_filename))
            admin.profile_picture = pic_filename

        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect('/admin_profile')

    return render_template('admin_side/crud_temp/admin_profile.html', admin=admin)

# route for help and support
@app.route('/help_and_support', methods=['GET', 'POST'])
def help_and_support():
    # Identify logged-in role
    admin_id = session.get('admin_id')
    user_id = session.get('user_id')
    owner_id = session.get('owner_id')

    role = None
    user_obj = None

    if admin_id:
        role = "Admin"
        user_obj = AdminInfo.query.get_or_404(admin_id)
    elif user_id:
        role = "User"
        user_obj = UserInfo.query.get_or_404(user_id)
    elif owner_id:
        role = "Owner"
        user_obj = PropertyOwner.query.get_or_404(owner_id)
    else:
        flash('You must be logged in to access this page.', 'danger')
        return redirect('/login')

    today_date = datetime.now().date()

    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')

        # generate unique message_code (6 chars)
        import random, string
        message_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        support_request = ContactSupport(
            message_code=message_code,
            msg_from=role,
            role_id=user_obj.id,
            name=user_obj.name,
            email=user_obj.email,
            subject=subject,
            message=message,
            status="Pending",
            created_at=datetime.now()
        )
        db.session.add(support_request)
        db.session.commit()

        flash('✅ Your support request has been submitted successfully!', 'success')
        return redirect('/help_and_support')

    return render_template(
        'admin_side/crud_temp/help_and_support.html',
        user=user_obj,
        role=role,
        today_date=today_date
    )

# route to see previous support and resolutions
@app.route('/my_support_requests')
def my_support_requests():
    # Identify logged-in role
    admin_id = session.get('admin_id')
    owner_id = session.get('owner_id')
    user_id = session.get('user_id')
    
    # fetch all support message
    if admin_id:
        support_requests = ContactSupport.query.filter_by(role_id=admin_id, msg_from='Admin').order_by(ContactSupport.created_at.desc()).all()
    elif owner_id:
        support_requests = ContactSupport.query.filter_by(role_id=owner_id, msg_from='Owner').order_by(ContactSupport.created_at.desc()).all()
    elif user_id:
        support_requests = ContactSupport.query.filter_by(role_id=user_id, msg_from='User').order_by(ContactSupport.created_at.desc()).all()
    elif not (admin_id or owner_id or user_id):
        flash('You must be logged in to access this page.', 'danger')
        return redirect('/login')
    
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/my_support_requests.html', support_requests=support_requests, today_date=today_date)
    

# route to resolve support requests
@app.route('/resolve_requests', methods=['GET', 'POST'])
@login_required_admin
def resolve_requests():
    # if admin is super admin i.e admin_code = 'SADMIN349' then they resolve all requests
    admin_id = session.get('admin_id')
    admin = AdminInfo.query.get_or_404(admin_id)
    # if super admin then resolve user, owner and admin requests
    if admin.admin_code == 'SADMIN349':
        support_requests = ContactSupport.query.order_by(ContactSupport.created_at.desc()).all()
    else:
        support_requests = ContactSupport.query.filter(ContactSupport.msg_from != 'Admin').order_by(ContactSupport.created_at.desc()).all()
    today_date = datetime.now().date()
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        resolution = request.form.get('resolution')
        
        support_request = ContactSupport.query.get_or_404(request_id)
        support_request.resolution = resolution
        support_request.status = 'Resolved'
        support_request.resolved_at = datetime.now()
        
        db.session.commit()
        
        flash('Support request resolved successfully!', 'success')
        return redirect('/resolve_requests')
    
    return render_template('admin_side/crud_temp/resolve_requests.html', support_requests=support_requests, today_date=today_date)

# view properties route
@app.route('/view_properties')
@login_required_admin
def admin_view_all_properties():
    properties = PropertyInfo.query.all()
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/view_properties.html', properties=properties, today_date=today_date)

# Show all pending properties
@app.route("/properties/pending")
@login_required_admin
def pending_properties():
    pending_props = PropertyInfo.query.filter_by(status="Pending").all()
    return render_template("admin_side/crud_temp/pending_properties.html", properties=pending_props)

@app.route("/properties/view/<int:property_id>")
@login_required_admin
def admin_view_property_details(property_id):
    prop = PropertyInfo.query.get_or_404(property_id)
    return render_template("admin_side/crud_temp/view_property_details.html", property=prop)


# Approve a property
@app.route("/properties/approve/<int:property_id>")
@login_required_admin
def admin_approve_property(property_id):
    prop = PropertyInfo.query.get_or_404(property_id)
    if prop.status == "Pending" or prop.status == "Deactive":
        prop.status = "Approved"
        db.session.commit()

        # Send notification to owner
        notification = OwnerNotification(
            owner_id=prop.owner_id,
            title="Property Approved",
            message=f"Your property '{prop.property_name}' has been approved.",
            type="success"
        )
        db.session.add(notification)
        db.session.commit()

        flash(f"Property '{prop.property_name}' has been approved!", "success")
    else:
        flash("Property is not in pending or deactive status.", "warning")

    return redirect(url_for("admin_view_property_details", property_id=prop.id))

# make property deactive
@app.route("/properties/deactivate/<int:property_id>")
@login_required_admin
def make_property_deactive(property_id):
    prop = PropertyInfo.query.get_or_404(property_id)
    if prop.status != "Deactive":
        prop.status = "Deactive"
        db.session.commit()

        # Send notification to owner
        notification = OwnerNotification(
            owner_id=prop.owner_id,
            title="Property Deactivated",
            message=f"Your property '{prop.property_name}' has been deactivated by the admin.",
            type="warning"
        )
        db.session.add(notification)
        db.session.commit()

        flash(f"Property '{prop.property_name}' has been deactivated.", "warning")
    else:
        flash("Property is already deactivated.", "warning")

    return redirect(url_for("admin_view_property_details", property_id=prop.id))

# route to view all admins to super admin
@app.route('/all_admins')
@login_required_admin
def view_all_admins():
    # fetch admin id from session
    admin_id = session.get('admin_id')
    admin = AdminInfo.query.get_or_404(admin_id)
    if admin.admin_code != 'SADMIN349':
        flash('Access denied. Only super admins can view all administrators.', 'danger')
        return redirect('/admin_dashboard')
    
    # fetch all admins but exept super admin
    admins = AdminInfo.query.filter(AdminInfo.admin_code != 'SADMIN349').all()
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/view_all_admins.html', admins=admins, today_date=today_date)

# view_admin
@app.route('/view_admin/<int:admin_id>')
@login_required_admin
def view_admin(admin_id):
    # fetch admin id from session
    current_admin_id = session.get('admin_id')
    current_admin = AdminInfo.query.get_or_404(current_admin_id)
    if current_admin.admin_code != 'SADMIN349':
        flash('Access denied. Only super admins can view administrator details.', 'danger')
        return redirect('/admin_dashboard')
    
    admin = AdminInfo.query.get_or_404(admin_id)
    today_date = datetime.now().date()
    return render_template('admin_side/crud_temp/view_admin.html', admin=admin, today_date=today_date)

# Utility function to generate unique 8-char code
def generate_unique_admin_code(length=8):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        # Check if code already exists
        if not AdminCode.query.filter_by(code=code).first():
            return code

# Route to generate admin code
@app.route('/generate_admin_code', methods=['GET', 'POST'])
@login_required_admin
def generate_admin_code():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        if not description:
            flash("Description is required to generate admin code.", "danger")
            return redirect(request.url)

        # Generate unique code
        new_code = generate_unique_admin_code()

        ist = pytz.timezone('Asia/Kolkata')
        current_datetime = datetime.now(ist)

        # Save to AdminCode table
        admin_code_entry = AdminCode(
            code=new_code,
            description=description,
            status='Unused',
            created_at=current_datetime
        )
        db.session.add(admin_code_entry)
        db.session.commit()
        flash(f"New admin code generated: {new_code}", "success")
        return redirect(request.url)

    # GET request: show all admin codes
    admin_codes = AdminCode.query.order_by(AdminCode.created_at.desc()).all()
    return render_template('admin_side/crud_temp/generate_admin_code.html', admin_codes=admin_codes)

# Route to delete admin code
@app.route('/delete_admin_code/<int:code_id>', methods=['POST'])
@login_required_admin
def delete_admin_code(code_id):
    code = AdminCode.query.get_or_404(code_id)
    if code.status == 'Used':
        flash('Cannot delete a code that is already used.', 'danger')
        return redirect(url_for('generate_admin_code'))

    try:
        db.session.delete(code)
        db.session.commit()
        flash('Admin code deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting admin code: {str(e)}', 'danger')
    return redirect(url_for('generate_admin_code'))


@app.route('/toggle_admin_status/<int:admin_id>')
@login_required_admin
def toggle_admin_status(admin_id):
    current_admin_id = session.get('admin_id')
    current_admin = AdminInfo.query.get_or_404(current_admin_id)

    if current_admin.admin_code != 'SADMIN349':
        flash('Access denied. Only super admins can update status.', 'danger')
        return redirect('/admin_dashboard')

    admin = AdminInfo.query.get_or_404(admin_id)

    if admin.status == "Active":
        admin.status = "Suspended"
        flash(f"{admin.name} has been suspended.", "warning")
    else:
        admin.status = "Active"
        flash(f"{admin.name} has been re-activated.", "success")

    db.session.commit()
    return redirect(url_for('view_admin', admin_id=admin.id))


# delete admin by id route
@app.route('/delete_admin/<int:admin_id>')
@login_required_admin
def delete_admin(admin_id):
    # fetch admin id from session
    current_admin_id = session.get('admin_id')
    current_admin = AdminInfo.query.get_or_404(current_admin_id)
    if current_admin.admin_code != 'SADMIN349':
        flash('Access denied. Only super admins can delete administrators.', 'danger')
        return redirect('/admin_dashboard')
    
    admin = AdminInfo.query.get_or_404(admin_id)
    db.session.delete(admin)
    db.session.commit()
    flash('Administrator has been deleted successfully!', 'success')
    return redirect(url_for('view_all_admins'))

# 
