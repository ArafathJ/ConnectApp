import os
import random
from datetime import date
import io
import base64
from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, DailyTask
from werkzeug.utils import secure_filename

# Optional QR Code generation
try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    QRCODE_ENABLED = True
except ImportError:
    QRCODE_ENABLED = False


# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-that-is-hard-to-guess'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'social.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/profile_pics')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# --- Initialize Extensions ---
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if not authenticated

# -- database creation---
with app.app_context():
    db.create_all()

# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Daily Task Management ---
def get_daily_task(user):
    """Gets or creates a new daily task for the user."""
    today = date.today()
    task = DailyTask.query.filter_by(user_id=user.id, task_date=today).first()
    if not task:
        task_list = [
            "Talk to someone new today and get their referral code.",
            "Introduce yourself to a stranger and exchange codes.",
            "Ask a cashier or barista for their referral code.",
            "Compliment a stranger and offer your referral code.",
            "Find someone with the same favorite color and connect."
        ]
        task_text = random.choice(task_list)
        task = DailyTask(user_id=user.id, task_text=task_text, task_date=today)
        db.session.add(task)
        db.session.commit()
    return task

# --- Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('An account with this email already exists.', 'error')
            return redirect(url_for('register'))

        new_user = User(
            name=name,
            age=age,
            email=email,
            referral_code=User.generate_referral_code()
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    task = get_daily_task(current_user)
    connections = current_user.friends.limit(5).all() # Show a few on the dashboard
    return render_template('dashboard.html', user=current_user, task=task, connections=connections)

@app.route('/add_connection', methods=['POST'])
@login_required
def add_connection():
    referral_code = request.form.get('referral_code').strip()
    
    if not referral_code:
        flash('Please enter a referral code.', 'error')
        return redirect(url_for('dashboard'))

    if referral_code == current_user.referral_code:
        flash("You can't connect with yourself.", 'warning')
        return redirect(url_for('dashboard'))

    friend_to_add = User.query.filter_by(referral_code=referral_code).first()

    if not friend_to_add:
        flash('Invalid referral code.', 'error')
        return redirect(url_for('dashboard'))

    if current_user.is_friend(friend_to_add):
        flash(f'You are already connected with {friend_to_add.name}.', 'info')
        return redirect(url_for('dashboard'))
    
    current_user.add_friend(friend_to_add)
    db.session.commit()
    flash(f'Successfully connected with {friend_to_add.name}!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/connections')
@login_required
def connections():
    all_connections = current_user.friends.all()
    return render_template('connections.html', connections=all_connections)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/qrcode')
@login_required
def generate_qr():
    if not QRCODE_ENABLED:
        return "QR Code library not installed.", 500

    referral_code = current_user.referral_code
    img = qrcode.make(referral_code)
    
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@app.route('/upload_profile', methods=['POST'])
@login_required
def upload_profile():
    if 'profile_pic' not in request.files:
        flash('No file part.', 'error')
        return redirect(url_for('profile'))

    file = request.files['profile_pic']

    if file.filename == '':
        flash('No selected file.', 'error')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # rename file to avoid name conflicts (use user id)
        filename = f"user_{current_user.id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # update user record
        current_user.profile_pic = filename
        db.session.commit()

        flash('Profile picture updated successfully!', 'success')
    else:
        flash('Invalid file type. Only JPG, PNG, GIF allowed.', 'error')

    return redirect(url_for('profile'))


# --- CLI Command to Create DB ---
@app.cli.command("create-db")
def create_db():
    """Creates the database tables."""
    with app.app_context():
        db.create_all()
        print("Database tables created.")

if __name__ == '__main__':
    app.run(debug=True)