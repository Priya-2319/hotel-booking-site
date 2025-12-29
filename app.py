from flask import Flask
import os
from dotenv import load_dotenv

#app initialization
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Configure
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

import models  # Import models to register them with SQLAlchemy
import backend.routes as routes  # Import routes to register them with the Flask app
import backend.user_routes as user_routes  # Import user routes to register them with the Flask app
import backend.admin_routes as admin_routes  # Import admin routes to register them with the Flask app


if __name__ == '__main__':
    app.run(debug=True) 