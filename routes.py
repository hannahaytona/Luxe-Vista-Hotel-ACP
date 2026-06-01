from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Room, Booking, Review
from datetime import datetime
import os

def init_routes(app):
    @app.route('/')
    def index():
        reviews = Review.query.order_by(Review.created_at.desc()).limit(6).all()
        featured_rooms = Room.query.limit(3).all()
        today = datetime.utcnow().date()
        for room in featured_rooms:
            # Room is unavailable only when booking is Approved or Checked-in (not while Awaiting Approval)
            overlapping = Booking.query.filter(
                Booking.room_id == room.id,
                Booking.status.in_(['Approved', 'Checked-in']),
                Booking.check_out > today
            ).first()
            room.availability = False if overlapping else True
        return render_template('landing.html', reviews=reviews, featured_rooms=featured_rooms)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('Logged in successfully.', 'success')
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('user_dashboard'))
            else:
                flash('Login failed. Check email and password.', 'danger')
        return render_template('login.html')

    @app.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            flash('If an account exists with this email, a password reset link has been sent.', 'info')
            return redirect(url_for('login'))
        return render_template('forgot_password.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.query.filter_by(email=email).first():
                flash('Email address already exists.', 'danger')
                return redirect(url_for('register'))
                
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password=hashed_password, role='user')
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role != 'admin':
            return redirect(url_for('user_dashboard'))
        rooms = Room.query.all()
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        users = User.query.all()
        
        total_rooms = Room.query.count()
        total_bookings = Booking.query.count()
        pending_requests = Booking.query.filter(Booking.status.in_(['Pending', 'Awaiting Approval'])).count()
        
        today = datetime.utcnow().date()
        # Count only Approved/Checked-in bookings as occupying the room
        occupied_count = Booking.query.filter(
            Booking.status.in_(['Approved', 'Checked-in']),
            Booking.check_out > today
        ).with_entities(Booking.room_id).distinct().count()
        
        available_rooms = total_rooms - occupied_count
        
        for room in rooms:
            # Room is unavailable only when booking is Approved or Checked-in
            overlapping = Booking.query.filter(
                Booking.room_id == room.id,
                Booking.status.in_(['Approved', 'Checked-in']),
                Booking.check_out > today
            ).first()
            room.availability = False if overlapping else True
            
        return render_template('admin_dashboard.html', rooms=rooms, bookings=bookings, users=users, 
                               total_rooms=total_rooms, total_bookings=total_bookings, 
                               pending_requests=pending_requests, available_rooms=available_rooms)
        
    @app.route('/admin/add_room', methods=['POST'])
    @login_required
    def add_room():
        if current_user.role != 'admin':
            return redirect(url_for('user_dashboard'))
        
        image = request.files.get('image')
        image_url = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image.save(image_path)
            image_url = filename
            
        new_room = Room(
            room_number=request.form.get('room_number'),
            category=request.form.get('category'),
            price=float(request.form.get('price')),
            capacity=int(request.form.get('capacity', 4)),
            amenities=request.form.get('amenities', 'Free WiFi, AC'),
            description=request.form.get('description'),
            image_url=image_url
        )
        db.session.add(new_room)
        db.session.commit()
        flash('Room added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_room/<int:room_id>', methods=['POST'])
    @login_required
    def edit_room(room_id):
        if current_user.role != 'admin':
            return redirect(url_for('user_dashboard'))
        room = Room.query.get(room_id)
        if room:
            room.room_number = request.form.get('room_number')
            room.category = request.form.get('category')
            room.price = float(request.form.get('price'))
            room.capacity = int(request.form.get('capacity', room.capacity))
            room.amenities = request.form.get('amenities', room.amenities)
            room.description = request.form.get('description')
            
            image = request.files.get('image')
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                image.save(image_path)
                room.image_url = filename
                
            db.session.commit()
            flash('Room updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_room/<int:room_id>')
    @login_required
    def delete_room(room_id):
        if current_user.role != 'admin':
            return redirect(url_for('user_dashboard'))
        room = Room.query.get(room_id)
        if room:
            Booking.query.filter_by(room_id=room.id).delete()
            db.session.delete(room)
            db.session.commit()
            flash('Room deleted successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/user/dashboard')
    @login_required
    def user_dashboard():
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
            
        category_filter = request.args.get('category', '')
        price_filter = request.args.get('max_price', '')
        check_in_str = request.args.get('check_in', '')
        check_out_str = request.args.get('check_out', '')
        guests_str = request.args.get('guests', '')
        
        query = Room.query
        if category_filter:
            query = query.filter_by(category=category_filter)
        if price_filter:
            query = query.filter(Room.price <= float(price_filter))
        if guests_str and guests_str.isdigit():
            query = query.filter(Room.capacity >= int(guests_str))
            
        rooms = query.all()
        
        check_in_date = None
        check_out_date = None
        if check_in_str and check_out_str:
            try:
                check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        available_count = 0
        for room in rooms:
            if check_in_date and check_out_date:
                overlapping = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.status.in_(['Approved', 'Checked-in']),
                    Booking.check_in < check_out_date,
                    Booking.check_out > check_in_date
                ).first()
            else:
                today = datetime.utcnow().date()
                # Room is unavailable only when booking is Approved or Checked-in
                overlapping = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.status.in_(['Approved', 'Checked-in']),
                    Booking.check_out > today
                ).first()
                
            room.availability = False if overlapping else True
            if room.availability:
                available_count += 1
                
        is_search = bool(category_filter or price_filter or check_in_str or guests_str)
            
        return render_template('user_dashboard.html', rooms=rooms, available_count=available_count, is_search=is_search)

    @app.route('/book_room/<int:room_id>', methods=['POST'])
    @login_required
    def book_room(room_id):
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
            
        check_in = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d').date()
        
        if check_in >= check_out:
            flash('Check-out date must be after check-in date.', 'danger')
            return redirect(url_for('user_dashboard'))
            
        overlap = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.status.in_(['Approved', 'Pending', 'Awaiting Approval', 'Checked-in']),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).first()
        
        if overlap:
            flash('Sorry, this room is already booked for the selected dates.', 'danger')
            return redirect(url_for('user_dashboard'))
        
        room = Room.query.get(room_id)
        nights = (check_out - check_in).days
        total_price = nights * room.price
        
        new_booking = Booking(
            user_id=current_user.id,
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            guest_count=int(request.form.get('guest_count')),
            status='Unpaid',
            total_price=total_price
        )
        db.session.add(new_booking)
        db.session.commit()
        return redirect(url_for('payment', booking_id=new_booking.id))
        
    @app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
    @login_required
    def payment(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        if booking.user_id != current_user.id:
            return redirect(url_for('user_dashboard'))
            
        if request.method == 'POST':
            booking.status = 'Awaiting Approval'
            db.session.commit()
            flash('Payment successful! Your booking is now awaiting admin approval.', 'success')
            return redirect(url_for('booking_history'))
            
        return render_template('payment.html', booking=booking)

    @app.route('/user/history')
    @login_required
    def booking_history():
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
        return render_template('booking_history.html', bookings=bookings)

    @app.route('/user/cancel_booking/<int:booking_id>')
    @login_required
    def cancel_booking(booking_id):
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        booking = Booking.query.get(booking_id)
        if booking and booking.user_id == current_user.id:
            if booking.status in ['Pending', 'Approved', 'Awaiting Approval']:
                booking.status = 'Cancelled'
                db.session.commit()
                flash('Booking cancelled successfully.', 'success')
        return redirect(url_for('booking_history'))

    @app.route('/user/profile', methods=['GET', 'POST'])
    @login_required
    def user_profile():
        if request.method == 'POST':
            current_user.username = request.form.get('username')
            if request.form.get('password'):
                current_user.password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
                
            picture = request.files.get('profile_picture')
            if picture and picture.filename != '':
                filename = secure_filename(picture.filename)
                pic_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                picture.save(pic_path)
                current_user.profile_picture = filename
                
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user_profile'))
            
        bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
        return render_template('profile.html', bookings=bookings)
        
    @app.route('/submit_review', methods=['POST'])
    @login_required
    def submit_review():
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        new_review = Review(user_id=current_user.id, rating=int(rating), comment=comment)
        db.session.add(new_review)
        db.session.commit()
        flash('Thank you for your review!', 'success')
        return redirect(url_for('user_dashboard'))

    @app.route('/admin/update_booking_status/<int:booking_id>/<string:status>')
    @login_required
    def update_booking_status(booking_id, status):
        if current_user.role != 'admin':
            return redirect(url_for('user_dashboard'))
        booking = Booking.query.get(booking_id)
        if booking and status in ['Approved', 'Rejected', 'Checked-in', 'Completed']:
            booking.status = status
            db.session.commit()
            flash(f'Booking status updated to {status}.', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete_user/<int:user_id>')
    @login_required
    def delete_user(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('user_dashboard'))
        if user_id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('admin_dashboard'))
        user = User.query.get(user_id)
        if user:
            Booking.query.filter_by(user_id=user.id).delete()
            Review.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/edit_user/<int:user_id>', methods=['POST'])
    @login_required
    def edit_user(user_id):
        if current_user.role != 'admin':
            return redirect(url_for('user_dashboard'))
        user = User.query.get(user_id)
        if user:
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.role = request.form.get('role')
            if request.form.get('password'):
                user.password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
            db.session.commit()
            flash('User updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
