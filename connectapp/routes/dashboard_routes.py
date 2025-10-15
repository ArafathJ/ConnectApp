from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from connectapp.models import User, DailyTask
from connectapp.extensions import db
from connectapp.utils.gemini_utils import generate_daily_task
from datetime import date, datetime, timedelta


def get_today_task(user):
    today = date.today()
    task = DailyTask.query.filter_by(user_id=user.id, task_date=today).first()
    if not task:
        # Generate AI-powered task using Gemini
        user_progress = _get_user_progress(user)
        task_data = generate_daily_task(user_progress)
        
        # Create new task with AI-generated content
        task = DailyTask(
            user_id=user.id,
            task_text=task_data['task_text'],
            difficulty=task_data['difficulty'],
            task_date=today,
            created_at=datetime.utcnow()
        )
        db.session.add(task)
        db.session.commit()
    return task


dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    users = User.query.order_by(User.score.desc()).all()
    task = get_today_task(current_user)
    suggestion = "Try your best and make a connection today!"
    time_remaining = (datetime.combine(date.today()+timedelta(days=1), datetime.min.time()) - datetime.now()).seconds
    ai_suggestion = None
    simplified_task = None

    if request.method == 'POST':
        if 'ai_suggest' in request.form:
            # Generate AI suggestion using Gemini
            try:
                user_progress = _get_user_progress(current_user)
                ai_suggestion_data = _generate_ai_suggestion(task.task_text, user_progress)
                ai_suggestion = ai_suggestion_data
            except Exception as e:
                ai_suggestion = "Here's a tip: Start with a warm smile and genuine interest in the other person!"
        elif 'simplify_task' in request.form:
            # Generate a simplified version of the task
            try:
                simplified_task_data = _generate_simplified_task(task.task_text, current_user)
                simplified_task = simplified_task_data
                # Update the task in database to mark as simplified
                task.simplified_count += 1
                task.task_text = simplified_task_data
                db.session.commit()
                # Refresh the task object to get the updated data
                db.session.refresh(task)
                flash('✨ Task simplified successfully! ✨', 'info')
            except Exception as e:
                simplified_task = "Say hello and exchange smiles with someone."
                flash('✨ Task simplified', 'info')
        elif 'referral_code' in request.form:
            ref_code = request.form['referral_code'].strip()
            if ref_code and ref_code != current_user.referral_code:
                friend = User.query.filter_by(referral_code=ref_code).first()
                if friend and not current_user.is_friend(friend):
                    current_user.add_friend(friend)
                    current_user.score += 20
                    friend.score += 20
                    db.session.commit()
                    flash(f'🎉 Connection established with {friend.name}! 🎉 (+20pts each) 🚀', 'success')
                elif friend:
                    flash('🤝 Already connected with this user.', 'info')
                else:
                    flash('❌ Referral code not found.', 'danger')
            else:
                flash('⚠️ Invalid referral code.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
    return render_template('dashboard.html', users=users, task=task, time_remaining=time_remaining, suggestion=suggestion, ai_suggestion=ai_suggestion, simplified_task=simplified_task)


@dashboard_bp.route('/api/daily_task', methods=['GET', 'POST'])
@login_required
def api_daily_task():
    """API endpoint to generate and serve daily tasks as JSON."""
    try:
        # Get user's progress data
        user_progress = _get_user_progress(current_user)
        
        # Generate new task using Gemini
        task_data = generate_daily_task(user_progress)
        
        # Create and save the task to database
        today = date.today()
        new_task = DailyTask(
            user_id=current_user.id,
            task_text=task_data['task_text'],
            difficulty=task_data['difficulty'],
            task_date=today,
            created_at=datetime.utcnow()
        )
        
        # Remove any existing task for today if it exists
        existing_task = DailyTask.query.filter_by(
            user_id=current_user.id, 
            task_date=today
        ).first()
        
        if existing_task:
            db.session.delete(existing_task)
        
        db.session.add(new_task)
        db.session.commit()
        
        # Return JSON response
        return jsonify({
            'success': True,
            'task': {
                'id': new_task.id,
                'task_text': new_task.task_text,
                'difficulty': new_task.difficulty,
                'created_at': new_task.created_at.isoformat(),
                'completed': new_task.completed,
                'xp_points': new_task.xp_points
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to generate daily task',
            'message': str(e)
        }), 500


def _get_user_progress(user):
    """Extract user progress data for Gemini API."""
    # Get completed tasks from the last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    completed_tasks = DailyTask.query.filter(
        DailyTask.user_id == user.id,
        DailyTask.completed == True,
        DailyTask.task_date >= thirty_days_ago
    ).all()
    
    # Calculate success rate
    total_tasks = DailyTask.query.filter(
        DailyTask.user_id == user.id,
        DailyTask.task_date >= thirty_days_ago
    ).count()
    
    success_rate = len(completed_tasks) / total_tasks if total_tasks > 0 else 0.5
    
    # Get recent activities (completed tasks)
    recent_activities = [task.task_text for task in completed_tasks[-5:]]
    
    # Determine difficulty preference based on user's history
    difficulty_preference = 'medium'  # Default
    if success_rate > 0.8:
        difficulty_preference = 'hard'
    elif success_rate < 0.3:
        difficulty_preference = 'easy'
    
    return {
        'completed_tasks': [task.task_text for task in completed_tasks],
        'difficulty_preference': difficulty_preference,
        'recent_activities': recent_activities,
        'success_rate': success_rate,
        'user_score': user.score
    }


def _generate_ai_suggestion(task_text, user_progress):
    """Generate AI-powered suggestions for completing a task."""
    try:
        from connectapp.utils.gemini_utils import GeminiAPI
        gemini = GeminiAPI()
        
        # Create a prompt for generating suggestions
        prompt = f"""
You are a social connection coach helping someone complete this daily challenge:

TASK: "{task_text}"

User's recent progress:
- Completed tasks: {len(user_progress.get('completed_tasks', []))} recent tasks
- Success rate: {user_progress.get('success_rate', 0.5):.1%}
- Difficulty preference: {user_progress.get('difficulty_preference', 'medium')}

Generate ONE specific, actionable suggestion to help them complete this task successfully. Make it encouraging and practical.

Requirements:
- Be specific and actionable (not vague)
- Focus on practical steps they can take
- Be encouraging and positive
- Keep it to 1-2 sentences maximum
- Make it relevant to the specific task

Respond with ONLY the suggestion text, no additional formatting.
"""
        
        response = gemini.model.generate_content(prompt)
        suggestion = response.text.strip()
        
        # Clean up the response
        if suggestion.startswith('"') and suggestion.endswith('"'):
            suggestion = suggestion[1:-1]
        
        return suggestion if suggestion and len(suggestion) > 10 else "Start with a warm smile and genuine interest in the other person!"
        
    except Exception as e:
        return "Here's a tip: Start with a warm smile and genuine interest in the other person!"


def _generate_simplified_task(original_task, user):
    """Generate a simplified version of the current task."""
    try:
        from connectapp.utils.gemini_utils import GeminiAPI
        gemini = GeminiAPI()
        
        # Create a prompt for generating simplified tasks
        prompt = f"""
You are a social connection coach. The user is struggling with this task:

ORIGINAL TASK: "{original_task}"

Generate a SIMPLIFIED version of this task that is easier to complete but still builds social connections.

Requirements:
- Make it significantly easier than the original
- Keep the same social connection goal
- Be specific and actionable
- Make it achievable for someone who might be shy or nervous
- Keep it to 1-2 sentences maximum
- Focus on low-pressure social interactions

Examples of simplified tasks:
- "Say hello and smile at one person today"
- "Make eye contact and nod at someone you pass by"
- "Ask one person 'How's your day going?'"

Respond with ONLY the simplified task text, no additional formatting.
"""
        
        response = gemini.model.generate_content(prompt)
        simplified = response.text.strip()
        
        # Clean up the response
        if simplified.startswith('"') and simplified.endswith('"'):
            simplified = simplified[1:-1]
        
        return simplified if simplified and len(simplified) > 10 else "Say hello and exchange smiles with someone."
        
    except Exception as e:
        return "Say hello and exchange smiles with someone."
