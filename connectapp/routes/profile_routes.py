from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from connectapp.extensions import db
from connectapp.models import User
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/connections')
@login_required
def connections():
    friends = current_user.friends.all()
    return render_template('connections.html', friends=friends)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename:
                filename = secure_filename(f'user_{current_user.id}_{file.filename}')
                filepath = os.path.join('static/profile_pics', filename)
                file.save(filepath)
                current_user.profile_pic = filename
                db.session.commit()
                flash('Profile picture updated!', 'success')
                return redirect(url_for('profile.profile'))
    return render_template('profile.html')
