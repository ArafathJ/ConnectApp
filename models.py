from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import string
import random
from datetime import date

db = SQLAlchemy()

# Association table for the many-to-many relationship
connections = db.Table('connections',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('connected_on', db.Date, default=date.today)
)

class User(UserMixin, db.Model):
    """User model for storing user details."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    referral_code = db.Column(db.String(8), unique=True, nullable=False)
    profile_pic = db.Column(db.String(200), default='default.jpg')
    tasks = db.relationship('DailyTask', backref='user', lazy=True)
    


    # Many-to-many relationship for connections
    friends = db.relationship('User', 
                              secondary=connections, 
                              primaryjoin=(connections.c.user_id == id), 
                              secondaryjoin=(connections.c.friend_id == id),
                              backref=db.backref('followers', lazy='dynamic'), 
                              lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_friend(self, friend):
        if not self.is_friend(friend):
            self.friends.append(friend)
            friend.friends.append(self) # Make the connection mutual

    def is_friend(self, friend):
        return self.friends.filter(connections.c.friend_id == friend.id).count() > 0

    @staticmethod
    def generate_referral_code():
        """Generates a unique 8-character alphanumeric referral code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not User.query.filter_by(referral_code=code).first():
                return code

    def __repr__(self):
        return f'<User {self.name}>'

class DailyTask(db.Model):
    """DailyTask model for storing user's daily tasks."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_text = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    task_date = db.Column(db.Date, nullable=False, default=date.today)

    def __repr__(self):
        return f'<Task {self.task_text}>'