import os
import random
from datetime import date
import io
import base64
from flask import Flask, render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, DailyTask
from werkzeug.utils import secure_filename
from google import genai
from sample import GEMINI_API_KEY
from datetime import datetime, date, timedelta
from referal import generate_referral_code



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

#--- Gemini Configuration ----------
client = genai.Client(api_key=GEMINI_API_KEY)



# --- for uploading provision file format------

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
        prompt = f"""
        You are an assistant creating a unique social challenge for the user.
        The challenge should encourage friendly interactions or small social acts.
        Examples:
        - Talk to a stranger and learn one fun fact about them.
        - Compliment someone genuinely today.
        - Ask someone about their favorite movie or music.
        - The difficultly level of daily mission increases by weeks or months

        Generate **one or two short daily mission and you must ask for atleast one connection** (max 20 words).
        Make it simple, positive, and social.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            # Handle possible response formats
            task_text = getattr(response, "text", None)
            if not task_text and hasattr(response + 'and add to the connection', "candidates"):
                task_text = response.candidates[0].content[0].text.strip()

            if not task_text:
                raise ValueError("Empty Gemini response")

        except Exception as e:
            print("❌ Gemini Task Generation Error:", e)
            # Fallback if Gemini fails
            fallback_tasks = [
                "Talk to someone new today and get their referral code.",
                "Introduce yourself to a stranger and exchange codes.",
                "Compliment someone and share your referral code."
            ]
            task_text = random.choice(fallback_tasks)

        # Save the task to the database
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
        referral = request.form.get('referral')

        # Check if user already exists
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('An account with this email already exists.', 'error')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(
            name=name,
            age=age,
            email=email,
            password=password,
            referral_code=User.generate_referral_code()
        )

        # Handle referral logic
        if referral:
            referrer = User.query.filter_by(referral_code=referral).first()
            if referrer:
                # ✅ Check if this referral was already used
                already_used = ReferralHistory.query.filter_by(referred_id=referrer.id).first()
                if already_used:
                    flash('This referral code has already been used once and cannot be reused.', 'error')
                else:
                    # ✅ Reward both users
                    referrer.score += 20
                    new_user.score += 20

                    # ✅ Mark referral in history
                    record = ReferralHistory(
                        referrer_id=referrer.id,
                        referred_id=new_user.id,
                        date=datetime.utcnow()
                    )
                    db.session.add(record)

                    # Optionally mark today’s task as complete for referrer
                    today = datetime.date.today()
                    task = DailyTask.query.filter_by(user_id=referrer.id, task_date=today).first()
                    if task and not task.completed:
                        task.completed = True
                        task.xp_points = 20
            else:
                flash("Invalid referral code entered.", "error")

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

@app.route("/ai_suggest", methods=["POST"])
@login_required
def ai_suggest():
    """Generate AI suggestion for a given task text."""
    data = request.get_json()
    task_text = data.get("task", "")
    if not task_text:
        return jsonify({"error": "Task text missing"}), 400

    prompt = f"""
    You are an assistant helping users plan their daily tasks.
    The task is: "{task_text}"
    Give only 1-2 short, practical steps on how to approach this task effectively.
    Keep it friendly and under 50 words.
    """

    try:
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        suggestion = getattr(response, "text", None)
        if not suggestion and hasattr(response, "candidates"):
            suggestion = response.candidates[0].content[0].text.strip()

        if  not suggestion:
            raise ValueError("Empty response from Gemini")
        
        return jsonify({"suggestion": suggestion})

    except Exception as e:
        print(e)
        return jsonify({"error": "AI suggestion failed"}), 500


@app.route("/simplify_task", methods=["POST"])
@login_required
def simplify_task():
    data = request.get_json()
    task_text = data.get("task", "")
    
    if not task_text:
        return jsonify({"error": "Task text missing"}), 400

    # Get today's task
    task = DailyTask.query.filter_by(
        user_id=current_user.id, task_text=task_text, task_date=date.today()
    ).first()

    if not task:
        return jsonify({"error": "Task not found"}), 404

    # Check if simplified 3 times this week
    week_start = date.today() - timedelta(days=date.today().weekday())  # Monday
    week_end = week_start + timedelta(days=6)
    weekly_simplified_count = DailyTask.query.filter(
        DailyTask.user_id==current_user.id,
        DailyTask.task_date.between(week_start, week_end),
        DailyTask.difficulty_level=="easy"
    ).count()

    if weekly_simplified_count >= 3:
        return jsonify({"error": "You can only simplify tasks 3 times per week"}), 403

    # Generate a simpler task using Gemini
    prompt = f"""
    You are an assistant. Make this task easier and simpler so the user can complete it quickly:
    Original task: "{task.task_text}"
    Give one short, easy, achievable version (max 15 words).
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        simplified_text = getattr(response, "text", None)
        if not simplified_text and hasattr(response, "candidates"):
            simplified_text = response.candidates[0].content[0].text.strip()

        if not simplified_text:
            raise ValueError("Empty response from Gemini")

        # Save simplified task
        task.task_text = simplified_text
        task.difficulty_level = "easy"
        task.simplified_count += 1
        db.session.commit()

        return jsonify({"task": simplified_text})

    except Exception as e:
        print(e)
        return jsonify({"error": "Simplifying task failed"}), 500

@app.route("/complete_task", methods=["POST"])
@login_required
def complete_task():
    data = request.get_json()
    task_id = data.get("task_id")
    task = DailyTask.query.filter_by(id=task_id, user_id=current_user.id).first()
    
    if not task:
        return jsonify({"error": "Task not found"}), 404

    if task.completed:
        return jsonify({"error": "Task already completed"}), 400

    # Mark as completed
    task.completed = True

    # Add XP to user score
    current_user.score += task.xp_points

    db.session.commit()

    return jsonify({
        "message": "Task completed!",
        "new_score": current_user.score,
        "xp_gained": task.xp_points
    })



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