from app import app, db
from models import Room

rooms_data = [
    {
        "room_number": "101",
        "category": "Standard",
        "price": 100.0,
        "capacity": 2,
        "amenities": "Free WiFi, Air Conditioning, Smart TV, Premium Bedding",
        "description": "A cozy and elegant room perfect for solo travelers or couples. Features a plush queen-size bed and modern decor.",
        "image_url": ""
    },
    {
        "room_number": "102",
        "category": "Standard",
        "price": 105.0,
        "capacity": 2,
        "amenities": "Free WiFi, Air Conditioning, Smart TV, City View",
        "description": "Enjoy a comfortable stay in this well-appointed standard room. Comes with a dedicated workspace and a beautiful city view.",
        "image_url": ""
    },
    {
        "room_number": "103",
        "category": "Standard",
        "price": 100.0,
        "capacity": 2,
        "amenities": "Free WiFi, Air Conditioning, Smart TV, Minibar",
        "description": "Relax in our signature standard room equipped with a smart TV, high-speed WiFi, and premium bathroom amenities.",
        "image_url": ""
    },
    {
        "room_number": "104",
        "category": "Standard",
        "price": 110.0,
        "capacity": 2,
        "amenities": "Free WiFi, Air Conditioning, Smart TV, Soundproof",
        "description": "A serene space designed for relaxation. This room offers blackout curtains, soundproof walls, and a minibar.",
        "image_url": ""
    },
    {
        "room_number": "105",
        "category": "Standard",
        "price": 100.0,
        "capacity": 2,
        "amenities": "Free WiFi, Air Conditioning, Smart TV",
        "description": "Perfect for short stays, this standard room blends luxury and convenience with easy access to hotel facilities.",
        "image_url": ""
    }
]

with app.app_context():
    for data in rooms_data:
        # Check if room already exists
        existing_room = Room.query.filter_by(room_number=data["room_number"]).first()
        if not existing_room:
            new_room = Room(**data)
            db.session.add(new_room)
            print(f"Added room {data['room_number']}")
        else:
            print(f"Room {data['room_number']} already exists.")
    
    db.session.commit()
    print("All standard rooms processed successfully!")
