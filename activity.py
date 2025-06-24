from flask import Blueprint, render_template, request, jsonify, session
from models import User, ActivityLog
from app import db
from auth import require_auth, require_role
from datetime import datetime, timedelta

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/logs')
@require_auth
@require_role(['admin', 'super_admin'])
def logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    user_filter = request.args.get('user', '')
    date_filter = request.args.get('date', '')
    
    query = ActivityLog.query
    
    if action_filter:
        query = query.filter(ActivityLog.action.contains(action_filter))
    
    if user_filter:
        query = query.join(User).filter(
            (User.username.contains(user_filter)) |
            (User.first_name.contains(user_filter)) |
            (User.last_name.contains(user_filter))
        )
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(
                db.func.date(ActivityLog.created_at) == filter_date
            )
        except ValueError:
            pass
    
    activities = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get unique actions for filter dropdown
    unique_actions = db.session.query(ActivityLog.action).distinct().all()
    unique_actions = [action[0] for action in unique_actions]
    
    return render_template('activity/logs.html', activities=activities,
                         unique_actions=unique_actions, action_filter=action_filter,
                         user_filter=user_filter, date_filter=date_filter)

@activity_bp.route('/api/stats')
@require_auth
@require_role(['admin', 'super_admin'])
def activity_stats():
    # Get activity stats for the last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Daily activity counts
    daily_stats = db.session.query(
        db.func.date(ActivityLog.created_at).label('date'),
        db.func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= start_date,
        ActivityLog.created_at <= end_date
    ).group_by(
        db.func.date(ActivityLog.created_at)
    ).order_by('date').all()
    
    # Top actions
    action_stats = db.session.query(
        ActivityLog.action,
        db.func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= start_date
    ).group_by(ActivityLog.action).order_by(db.func.count(ActivityLog.id).desc()).limit(10).all()
    
    # Most active users
    user_stats = db.session.query(
        User.username,
        User.first_name,
        User.last_name,
        db.func.count(ActivityLog.id).label('count')
    ).join(ActivityLog).filter(
        ActivityLog.created_at >= start_date
    ).group_by(User.id).order_by(db.func.count(ActivityLog.id).desc()).limit(10).all()
    
    return jsonify({
        'daily_stats': [{'date': str(stat.date), 'count': stat.count} for stat in daily_stats],
        'action_stats': [{'action': stat.action, 'count': stat.count} for stat in action_stats],
        'user_stats': [{'username': stat.username, 'name': f"{stat.first_name} {stat.last_name}", 'count': stat.count} for stat in user_stats]
    })

def log_activity(user_id, action, description, entity_type=None, entity_id=None, ip_address=None, user_agent=None):
    """Helper function to log user activities"""
    activity = ActivityLog(
        user_id=user_id,
        action=action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.session.add(activity)
    db.session.commit()
    return activity
