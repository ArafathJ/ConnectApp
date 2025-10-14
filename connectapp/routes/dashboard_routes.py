from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from connectapp.models import User, DailyTask
from connectapp.extensions import db
from datetime import date, datetime, timedelta

import random

dashboad_example_tasks = [
    "Compliment someone genuinely today.",
    "Talk to a stranger and learn one fun fact about them.",
    "Ask someone about their favorite movie or music.",
    "Make a new friend and exchange contact info.",
    "Invite someone to join SocialApp with your referral code."
]

dashboad_suggestions = {
    "Compliment someone genuinely today.": "Think of something positive about a person and share it sincerely!",
    "Talk to a stranger and learn one fun fact about them.": "Approach someone, smile, and ask a light question like 'What's your favorite hobby?'",
    "Ask someone about their favorite movie or music.": "Get a conversation going with 'What movie or song always makes you happy?'",
    "Make a new friend and exchange contact info.": "Introduce yourself and see if there's a shared interest to connect over.",
    "Invite someone to join SocialApp with your referral code.": "Explain what SocialApp does, and offer them your code to join you!"
}

def get_today_task(user):
    today = date.today()
    task = DailyTask.query.filter_by(user_id=user.id, task_date=today).first()
    if not task:
        # Create one if not exists (simulate AI/gemini task logic)
        task_text = random.choice(list(dashboad_suggestions.keys()))
        task = DailyTask(user_id=user.id, task_text=task_text, task_date=today)
        db.session.add(task)
        db.session.commit()
    return task


dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    users = User.query.order_by(User.score.desc()).all()
    task = get_today_task(current_user)
    suggestion = dashboad_suggestions.get(task.task_text, "Try your best and make a connection today!")
    time_remaining = (datetime.combine(date.today()+timedelta(days=1), datetime.min.time()) - datetime.now()).seconds
    ai_suggestion = None
    simplified_task = None

    if request.method == 'POST':
        if 'ai_suggest' in request.form:
            ai_suggestion = suggestion 
        elif 'simplify_task' in request.form:
            simplified_task = 'Say hello and exchange smiles with someone.'
            flash('Task simplified', 'info')
            # You could update the DB task to mark as simplified
        elif 'referral_code' in request.form:
            ref_code = request.form['referral_code'].strip()
            if ref_code and ref_code != current_user.referral_code:
                friend = User.query.filter_by(referral_code=ref_code).first()
                if friend and not current_user.is_friend(friend):
                    current_user.add_friend(friend)
                    current_user.score += 20
                    friend.score += 20
                    db.session.commit()
                    flash(f'You are now connected with {friend.name}! (+20pts each)', 'success')
                elif friend:
                    flash('Already connected with this user.', 'info')
                else:
                    flash('Referral code not found.', 'danger')
            else:
                flash('Invalid referral code.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
    return render_template('dashboard.html', users=users, task=task, time_remaining=time_remaining, suggestion=suggestion, ai_suggestion=ai_suggestion, simplified_task=simplified_task)
