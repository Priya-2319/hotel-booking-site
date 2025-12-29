# Hotel Booking System

A comprehensive Flask-based hotel booking platform that connects property owners with guests, featuring role-based access for users, property owners, and administrators.

## Features

### For Users
- Browse and search available properties and rooms
- Book accommodations with real-time availability
- Manage booking history
- Leave reviews and ratings for properties
- Receive notifications about bookings
- Contact support for assistance

### For Property Owners
- Register and manage properties
- Add and configure room details
- Track bookings and occupancy
- Receive notifications about property status
- Manage property listings and availability

### For Administrators
- Approve/reject property listings
- Manage users, owners, and properties
- Handle support tickets and inquiries
- Generate admin codes for new administrators
- Monitor platform activity and notifications

## Tech Stack

- **Backend Framework:** Flask 3.1.1
- **Database:** SQLAlchemy ORM
- **Authentication:** Flask-Login
- **Forms:** Flask-WTF & WTForms
- **Environment Management:** python-dotenv
- **Additional Libraries:** pycountry for location data

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git

### Installation

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/Priya-2319/hotel-booking-site.git
   cd hotel-booking-site
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set Up Environment Variables**
   
   Create a `.env` file in the root directory with the following configuration:
   ```
   SQLALCHEMY_DATABASE_URI=sqlite:///hotel_booking.db
   SQLALCHEMY_TRACK_MODIFICATIONS=False
   SECRET_KEY=your-secret-key-here
   ```
   
   Replace `your-secret-key-here` with a secure random string.

6. **Run the Application**
   ```bash
   flask run
   ```
   
   Or alternatively:
   ```bash
   python app.py
   ```

7. **Access the Application**
   
   Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Database Models

The application includes the following main models:

- **PropertyOwner:** Property owners with authentication
- **UserInfo:** Regular users who book accommodations
- **AdminInfo:** Platform administrators
- **PropertyInfo:** Property listings and details
- **RoomInfo:** Individual rooms within properties
- **UserBooking:** Active bookings
- **BookingHistory:** Archived bookings
- **Review:** User reviews and ratings
- **Notifications:** System notifications for all user types
- **ContactSupport:** Support ticket system
- **GeneralInquiry:** General contact form submissions

## Project Structure

```
hotel-booking-system/
├── app.py                 # Application initialization
├── models.py              # Database models
├── backend/
│   ├── routes.py          # General routes
│   ├── user_routes.py     # User-specific routes
│   └── admin_routes.py    # Admin-specific routes
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables (create this)
└── README.md             # Project documentation
```

## Development

The application runs in debug mode by default when using `python app.py`. For production deployment, ensure debug mode is disabled and use a production-ready server like Gunicorn.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository or use the contact support feature within the application.