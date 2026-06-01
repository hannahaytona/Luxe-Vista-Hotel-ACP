import sys
import subprocess
import os

# Auto-install dependencies if they are missing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUIREMENTS_PATH = os.path.join(BASE_DIR, "requirements.txt")

try:
    import flask
    import flask_sqlalchemy
    import flask_login
except ImportError:
    print("First run detected: Installing missing dependencies... Please wait a moment.")
    try:
        # First ensure pip is installed (since your Python 3.14 is missing it)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print("Pip is missing. Installing pip first...")
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--default-pip"])
        
        # Now install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_PATH])
        print("Dependencies installed successfully! Please click Run / Debug one more time.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during installation: {e}")
        sys.exit(1)

from flask import Flask
from models import db, User
from routes import init_routes
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hotel_booking_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel_v4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

init_routes(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create an admin user if not exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin_user = User(username='admin', email='admin@hotel.com', password=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created: admin@hotel.com / admin123")
            
        # Add 5 Standard Rooms automatically
        from models import Room
        rooms_data = [
            {"room_number": "101", "category": "Standard", "price": 100.0, "capacity": 2, "amenities": "Free WiFi, AC, Smart TV, Premium Bedding", "description": "A cozy and elegant room perfect for solo travelers or couples. Features a plush queen-size bed and modern decor."},
            {"room_number": "102", "category": "Standard", "price": 105.0, "capacity": 2, "amenities": "Free WiFi, AC, Smart TV, City View", "description": "Enjoy a comfortable stay in this well-appointed standard room. Comes with a dedicated workspace and a beautiful city view."},
            {"room_number": "103", "category": "Standard", "price": 100.0, "capacity": 2, "amenities": "Free WiFi, AC, Smart TV, Minibar", "description": "Relax in our signature standard room equipped with a smart TV, high-speed WiFi, and premium bathroom amenities."},
            {"room_number": "104", "category": "Standard", "price": 110.0, "capacity": 2, "amenities": "Free WiFi, AC, Smart TV, Soundproof", "description": "A serene space designed for relaxation. This room offers blackout curtains, soundproof walls, and a minibar."},
            {"room_number": "105", "category": "Standard", "price": 100.0, "capacity": 2, "amenities": "Free WiFi, AC, Smart TV", "description": "Perfect for short stays, this standard room blends luxury and convenience with easy access to hotel facilities."}
        ]
        for data in rooms_data:
            if not Room.query.filter_by(room_number=data["room_number"]).first():
                db.session.add(Room(**data))
        db.session.commit()
    import threading
    import webbrowser
    import time
    
    def open_browser():
        time.sleep(1.5) # Wait for server to start
        webbrowser.open_new("http://127.0.0.1:5000")
        
    # Prevent browser from opening twice due to Flask's auto-reloader
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Thread(target=open_browser).start()
        
    app.run(debug=True, port=5000)
